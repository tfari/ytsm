""" View for displaying Video Details """
from urwid import AttrMap, Button

from ytsm.uis.tui_urwid.widgets import MenuButton, VerticalScrollFrame
from ytsm.uis.tui_urwid.views.base_view import BaseView

from ytsm.uis.ytsm_controller import YTSMController
from ytsm.settings import NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO

class VideoDetailView(BaseView):
    """ View for displaying Video Details """
    def __init__(self, master, ytsm_controller: YTSMController, video_dto: YTSMController.VideoDTO):
        self.ytsm_controller = ytsm_controller
        self.video_dto = video_dto

        color = NEW_VIDEO if video_dto.video.new else UNWATCHED_VIDEO if not video_dto.video.watched else OLD_VIDEO
        self.video_details = VerticalScrollFrame(parent_keypress_callback=self.keypress_callback)
        self.video_details.load_data([
            AttrMap(MenuButton(f'Title: {video_dto.video.name}', None), color),
            AttrMap(MenuButton(f'Channel: {video_dto.channel_name}', None), 'bold'),
            AttrMap(MenuButton(f'Date: {video_dto.video.sensible_pubdate()}', None), 'bold'),
            AttrMap(MenuButton(f'', None), ''),
            AttrMap(MenuButton(f'Description:', None), 'bold'),
            AttrMap(MenuButton(f'', None), ''),
            AttrMap(MenuButton(video_dto.video.description, None), 'video_description'),
        ], reset_position=True)

        super().__init__(master=master,
                         title_bar_str='YTSM - Video Details',
                         body=self.video_details)
