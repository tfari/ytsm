""" Channel Selector Pane """
from typing import Callable

from urwid import AttrMap, Frame, Edit, connect_signal
from ytsm.uis.tui_urwid.widgets import VerticalScrollFrame, CommandBar, MenuButton
from ytsm.uis.tui_urwid.views.base_view import BaseView

from ytsm.uis.ytsm_controller import YTSMController
from ytsm.settings import SETTINGS, NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO


class ChannelSelectorPane(BaseView):
    """ Channel Selector Pane """
    def __init__(self, master, ytsm_controller: YTSMController, bottom_bar: CommandBar,
                 callback_channel_select: Callable, callback_no_channels: Callable):
        self.ytsm_controller = ytsm_controller
        self.bottom_bar = bottom_bar
        self.callback_channel_select = callback_channel_select
        self.callback_no_channels = callback_no_channels

        self.channel_dto_list = []
        self.focused_channel_dto = None
        self.channel_select_VSF = VerticalScrollFrame(
            parent_render_callback=self.channel_select_VSF_render_callback,
            parent_keypress_callback=self.channel_select_VSF_keypress_callback)

        self.channel_search_bar = Edit(('prompt_message', 'Search: '))
        connect_signal(self.channel_search_bar, 'change', lambda x, y: self.channel_search_bar_edit(y))

        self.pane = Frame(body=self.channel_select_VSF, header=self.channel_search_bar)

        # Bindings
        self.BINDINGS = {
            SETTINGS.tui_settings.keybindings.remove_channel_key.upper(): self.remove_channel_command,
            SETTINGS.tui_settings.keybindings.update_channel_key.upper(): self.update_channel_command,
            SETTINGS.tui_settings.keybindings.mark_watched_key.upper(): self.mark_channel_watched_command,
            SETTINGS.tui_settings.keybindings.open_on_browser_key.upper(): self.visit_channel_command,
            SETTINGS.tui_settings.keybindings.toggle_mute_notifications_key.upper(): self.toggle_mute_command,
        }

        super().__init__(
            master=master,
            body=self.pane,
            title_bar_str='Channels',
            use_top_bar=False
        )

    def keypress(self, size, key):
        """
        Catch "up" and "down" keys to provide navigation between channel_search_bar and channel_select_VSF
            * If "up" and focus on body and focused_channel_dto = 0 -> Focus the searchbar
            * If "down" and focus on header -> Focus the channel_select_VSF, focus_position on VSF's scroll_listbox = 0
        """
        if key.lower() in ('up', 'down') and self.channel_dto_list:
            if key == 'up' and self.pane.focus_part == 'body' and self.focused_channel_dto == self.channel_dto_list[0]:
                self.pane.focus_position = 'header'
            elif key == 'down' and self.pane.focus_part == 'header':
                self.pane.focus_position = 'body'
                self.channel_select_VSF.scroll_listbox.focus_position = 0
            else:
                super().keypress(size, key)
        else:
            super().keypress(size, key)

    def reload_view(self, reset_position: bool = False) -> None:
        """ Reload the VSF data """
        self.channel_dto_list = self.ytsm_controller.get_channel_dto_list()

        channel_select_vsf_data = []
        for channel_dto in self.channel_dto_list:
            color = NEW_VIDEO if channel_dto.new else UNWATCHED_VIDEO if channel_dto.unwatched else OLD_VIDEO
            muted = '(m) ' if not channel_dto.channel.notify_on else ''
            display_text = f'{muted}{channel_dto.channel.name}'
            channel_select_vsf_data.append(
                AttrMap(MenuButton(display_text, channel_dto), color)
            )

        self.channel_select_VSF.load_data(channel_select_vsf_data, reset_position=reset_position)

    def channel_select_VSF_render_callback(self, focus_index: int) -> None:
        """ Callback for channel_select_VSF render events """
        if self.channel_dto_list:
            self.focused_channel_dto = self.channel_dto_list[focus_index]
            self.callback_channel_select(self.channel_dto_list[focus_index])
        else:
            self.callback_no_channels()

    def channel_select_VSF_keypress_callback(self, channel_dto: YTSMController.ChannelDTO, key: str) -> None:
        """ Callback for channel_select_VSF keypress events """
        if key.upper() in self.BINDINGS.keys():
            self.BINDINGS[key.upper()](channel_dto)
        else:
            self.keypress_callback(channel_dto, key)

    def channel_search_bar_edit(self, input_str: str) -> None:
        """ Channel search terms on channel_search_bar changed """
        self.ytsm_controller.set_channel_search_term(input_str)
        self.reload_view()

    def remove_channel_command(self, channel_dto: YTSMController.ChannelDTO) -> None:
        """ Remove a Channel """
        self.focused_channel_dto = channel_dto
        self.bottom_bar.display_prompt(self._remove_channel_callback, f'Remove channel: "{channel_dto.channel.name}"',
                                       ['Y', 'N'])
        self.master.master.main_frame.focus_part = 'footer'  # TODO: Decouple this

    def _remove_channel_callback(self, input_str: str) -> None:
        """ Callback for bottom_bar prompt on remove_channel_command """
        if input_str.upper() == 'Y':
            self.ytsm_controller.remove_channel(self.focused_channel_dto)
            self.bottom_bar.display_message(f'Removed channel: "{self.focused_channel_dto.channel.name}"')
            self.focused_channel_dto = None
            self.reload_view(reset_position=True)
        else:
            self.focused_channel_dto = None
            self.bottom_bar.clear()
        self.master.master.main_frame.focus_part = 'body'

    def update_channel_command(self, channel_dto: YTSMController.ChannelDTO) -> None:
        """ Update a Channel """
        self.focused_channel_dto = channel_dto
        try:
            amt = self.ytsm_controller.update_channel(self.focused_channel_dto)
            self.bottom_bar.display_message(f'Updated channel: "{self.focused_channel_dto.channel.name}", '
                                            f'{amt} new videos.')
            self.reload_view()
        except YTSMController.UpdateChannelError as e:
            self.bottom_bar.display_error(f'Update channel failed with error: {e}')

    def mark_channel_watched_command(self, channel_dto: YTSMController.ChannelDTO) -> None:
        """ Mark all videos in a Channel as watched """
        self.focused_channel_dto = channel_dto
        self.ytsm_controller.mark_channel_all_watched(self.focused_channel_dto)
        self.bottom_bar.display_message(f'Marked all as Watched in channel: "{self.focused_channel_dto.channel.name}"')
        self.reload_view()

    def visit_channel_command(self, channel_dto: YTSMController.ChannelDTO) -> None:
        """ Visit the Channel """
        self.focused_channel_dto = channel_dto
        self.ytsm_controller.visit_channel(channel_dto)
        self.bottom_bar.display_message(f'Visited channel: "{self.focused_channel_dto.channel.name}"')

    def toggle_mute_command(self, channel_dto: YTSMController.ChannelDTO) -> None:
        """ Mute / unmute a Channel """
        self.ytsm_controller.toggle_mute_channel(channel_dto)
        state = 'Muted' if channel_dto.channel.notify_on else 'Unmuted'
        self.bottom_bar.display_message(f'{state} channel: "{channel_dto.channel.name}"')
        self.reload_view()
