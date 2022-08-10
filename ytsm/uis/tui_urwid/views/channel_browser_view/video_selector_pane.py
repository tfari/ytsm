""" Channel Selector Pane """
from typing import Callable

from urwid import AttrMap, Button, Columns, Frame, Edit, connect_signal
from ytsm.uis.tui_urwid.widgets import VerticalScrollFrame, MenuButton, CommandBar
from ytsm.uis.tui_urwid.views.base_view import BaseView

from ytsm.uis.ytsm_controller import YTSMController
from ytsm.settings import SETTINGS, NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO


class VideoSelectorPane(BaseView):
    """ Video selector Pane """
    def __init__(self, master, ytsm_controller: YTSMController, bottom_bar: CommandBar,
                 callback_open_video_detail_view: Callable, callback_video_alterations: Callable):
        self.ytsm_controller = ytsm_controller
        self.bottom_bar = bottom_bar
        self.callback_open_video_detail_view = callback_open_video_detail_view
        self.callback_video_alterations = callback_video_alterations

        self.video_alterations_happening = False

        self.video_dto_list = []
        self.focused_video_dto = None
        self.channel_id = ''
        self.video_select_VSF = VerticalScrollFrame(
            parent_render_callback=self.video_select_VSF_render_callback,
            parent_keypress_callback=self.video_select_VSF_keypress_callback
        )

        # Search / Filter
        self.video_search_bar = Edit(('prompt_message', 'Search by NAME: '))
        connect_signal(self.video_search_bar, 'change', lambda obj, txt: self.video_search_bar_edit(txt))
        self.video_button_search_type = Button('NAME', on_press=self.video_search_type_command)
        self.video_button_filter_type = Button((OLD_VIDEO, 'ALL'), on_press=self.video_filter_command)
        self.search_bar = Columns([('weight', 4, self.video_search_bar), self.video_button_search_type,
                                   self.video_button_filter_type])

        self.pane = Frame(body=self.video_select_VSF, header=self.search_bar)

        self.BINDINGS = {
            SETTINGS.tui_settings.keybindings.open_on_browser_key.upper(): self.watch_video_command,
            SETTINGS.tui_settings.keybindings.mark_watched_key.upper(): self.mark_video_watched_command,
            SETTINGS.tui_settings.keybindings.video_details_key.upper(): self.callback_open_video_detail_view
        }

        super().__init__(
            master=master,
            body=self.pane,
            title_bar_str='Videos',
            use_top_bar=False
        )

    def keypress(self, size, key):
        """
        Catch "up" and "down" keys to provide navigation between search_bar and video_select_VSF
            * If "up" and focus on body and focused_channel_dto = 0 -> Focus the searchbar
            * If "down" and focus on header -> Focus the channel_select_VSF, focus_position on VSF's scroll_listbox = 0
        """
        if key.lower() in ('up', 'down') and self.video_dto_list:
            if key == 'up' and self.pane.focus_part == 'body' and self.focused_video_dto == self.video_dto_list[0]:
                self.pane.focus_position = 'header'
                self.search_bar.set_focus(0)
            elif key == 'down' and self.pane.focus_part == 'header':
                self.pane.focus_position = 'body'
                self.video_select_VSF.scroll_listbox.focus_position = 0
            else:
                super().keypress(size, key)
        else:
            super().keypress(size, key)

    def video_select_VSF_render_callback(self, focus_index: int) -> None:
        """ Callback for channel_select_VSF render events """
        self.video_alterations_happening = False
        if self.video_dto_list and focus_index is not None:
            self.focused_video_dto = self.video_dto_list[focus_index]

    def video_select_VSF_keypress_callback(self, video_dto: YTSMController.VideoDTO, key: str) -> None:
        """ Callback for channel_select_VSF keypress events """
        if key.upper() in self.BINDINGS.keys():
            self.BINDINGS[key.upper()](video_dto)
        else:
            self.keypress_callback(video_dto, key)

    def video_search_bar_edit(self, search_terms: str) -> None:
        """ Perform a Video search """
        if self.channel_id:
            self.ytsm_controller.set_video_search_term(search_terms)
            self.reload_view(self.channel_id)
        else:
            print("!")
            exit(0)

    def video_search_type_command(self, obj: Button) -> None:
        """ Change the video search type """
        if obj.get_label() == 'NAME':
            obj.set_label('DESC')
            self.video_search_bar.set_caption(('prompt_message', 'Search by DESC: '))
            self.ytsm_controller.set_video_search_type(YTSMController.DESC)
        elif obj.get_label() == 'DESC':
            obj.set_label('DATE')
            self.video_search_bar.set_caption(('prompt_message', 'Search by DATE: '))
            self.ytsm_controller.set_video_search_type(YTSMController.DATE)
        elif obj.get_label() == 'DATE':
            obj.set_label('NAME')
            self.video_search_bar.set_caption(('prompt_message', 'Search by NAME: '))
            self.ytsm_controller.set_video_search_type(YTSMController.NAME)

        self.reload_view(channel_id=self.channel_id)

    def video_filter_command(self, obj: Button) -> None:
        """ Change the video filter """
        if obj.get_label() == 'ALL':
            obj.set_label((NEW_VIDEO, 'NEW'))
            self.ytsm_controller.set_video_filter(YTSMController.NEW)
        elif obj.get_label() == 'NEW':
            obj.set_label((UNWATCHED_VIDEO, 'UNWATCHED'))
            self.ytsm_controller.set_video_filter(YTSMController.UNWATCHED)
        elif obj.get_label() == 'UNWATCHED':
            obj.set_label((OLD_VIDEO, 'ALL'))
            self.ytsm_controller.set_video_filter(YTSMController.ALL)

        self.reload_view(channel_id=self.channel_id)

    def view_enter(self) -> None:
        """ View has been entered. Reload filters and search terms. """
        # Reload filter
        if self.video_button_filter_type.get_label() == 'ALL':
            self.ytsm_controller.set_video_filter(YTSMController.ALL)
        elif self.video_button_filter_type.get_label() == 'NEW':
            self.ytsm_controller.set_video_filter(YTSMController.NEW)
        elif self.video_button_filter_type.get_label() == 'UNWATCHED':
            self.ytsm_controller.set_video_filter(YTSMController.UNWATCHED)

        # Reload search type
        if self.video_button_search_type.get_label == 'Search by NAME: ':
            self.ytsm_controller.set_video_search_type(YTSMController.NAME)
        elif self.video_button_search_type.get_label == 'Search by DESC: ':
            self.ytsm_controller.set_video_search_type(YTSMController.DESC)
        elif self.video_button_search_type.get_label == 'Search by DATE: ':
            self.ytsm_controller.set_video_search_type(YTSMController.DATE)

        # Reload search terms
        self.video_search_bar_edit(self.video_search_bar.get_edit_text())

    def reload_view(self, channel_id: str, reset_position: bool = False) -> None:
        """
        Reload the VSF data
        """
        if self.video_alterations_happening:  # Don't reload when the reload_view() happens on a video alteration call
            return None

        self.channel_id = channel_id
        self.video_dto_list = self.ytsm_controller.get_video_dto_list(channel_id)

        video_select_vsf_data = []
        for video_dto in self.video_dto_list:
            color = NEW_VIDEO if video_dto.video.new else UNWATCHED_VIDEO if not video_dto.video.watched else OLD_VIDEO
            video_select_vsf_data.append(
                AttrMap(MenuButton(f'{video_dto.video.name}', video_dto), color)
            )

        self.video_select_VSF.load_data(video_select_vsf_data, reset_position=reset_position)
        if not self.video_dto_list:
            self.focused_video_dto = None

    def no_channels(self) -> None:
        """ There are no Channels in the Channel Selection pane """
        self.channel_id = None
        self.video_select_VSF.load_data([])

    def watch_video_command(self, video_dto: YTSMController.VideoDTO) -> None:
        """ Watch the video associated with the video_dto """
        self.focused_video_dto = video_dto
        self.ytsm_controller.watch_video(video_dto)
        self.reload_view(channel_id=self.channel_id)
        self.video_alterations_happening = True
        self.bottom_bar.display_message(f'Watched video: "{video_dto.video.name}"')
        self.callback_video_alterations()

    def mark_video_watched_command(self, video_dto: YTSMController.VideoDTO) -> None:
        """ Mark the Video associated with the VideoDTO as watched """
        self.focused_video_dto = video_dto
        self.ytsm_controller.mark_video_watched(video_dto)
        self.reload_view(channel_id=self.channel_id)
        self.video_alterations_happening = True
        self.bottom_bar.display_message(f'Marked video as watched: "{video_dto.video.name}"')
        self.callback_video_alterations()
