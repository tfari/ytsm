""" All Videos View """
from typing import Callable
from urwid import Columns, LineBox, AttrMap

from ytsm.uis.tui_urwid.widgets import MenuButton
from ytsm.uis.tui_urwid.views.channel_browser_view.channel_browser_view import ChannelBrowserView
from ytsm.uis.tui_urwid.views.channel_browser_view.video_selector_pane import VideoSelectorPane

from ytsm.uis.ytsm_controller import YTSMController

from ytsm.settings import SETTINGS, NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO


class AllVideosView(ChannelBrowserView):
    """ All Videos View """
    def __init__(self, master, ytsm_controller: YTSMController, bottom_bar, callback_open_video_detail_view: Callable):
        super().__init__(master, ytsm_controller, bottom_bar, callback_open_video_detail_view)
        self.video_select_pane = AllVideosVideoSelectorPane(self, ytsm_controller, bottom_bar,
                                                            self.callback_open_video_detail_view,
                                                            self.callback_video_alterations)
        self.columns = Columns([LineBox(self.video_select_pane, 'Videos')])
        self.title_bar_text.set_text('YTSM - All Videos')

        self.BINDINGS = {
            SETTINGS.tui_settings.keybindings.update_all_channels_key.upper(): self.update_all_channels_command,
            SETTINGS.tui_settings.keybindings.add_channel_key.upper(): self.add_channel_command,
        }
        self.body = self.columns

    def reload_view(self, reset_position: bool = False):
        """ Call a reload on video_select_pane """
        self.video_select_pane.reload_view('', reset_position=reset_position)


class AllVideosVideoSelectorPane(VideoSelectorPane):
    """ Frame for All Videos Video Selector, reimplements VideoSelectorPane but changes reload_data and
    video_search_bar functionality """
    def video_search_bar_edit(self, search_terms: str) -> None:
        """ Perform a Video search """
        self.ytsm_controller.set_video_search_term(search_terms)
        self.reload_view('')

    def reload_view(self, channel_id: str, reset_position: bool = False):
        """
        Reload the VSF data
        """
        self.video_dto_list = self.ytsm_controller.get_video_dto_list('', all_videos=True)

        video_select_vsf_data = []
        for video_dto in self.video_dto_list:
            color = NEW_VIDEO if video_dto.video.new else UNWATCHED_VIDEO if not video_dto.video.watched else OLD_VIDEO
            video_select_vsf_data.append(
                AttrMap(MenuButton(f'{video_dto.video.sensible_pubdate()} - {video_dto.channel_name} - '
                                   f'{video_dto.video.name}', video_dto), color)
            )

        self.video_select_VSF.load_data(video_select_vsf_data, reset_position=reset_position)
        if not self.video_dto_list:
            self.focused_video_dto = None
