""" Frames for All Videos View and All Videos Selector"""
from tkinter import END

from ytsm.settings import NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO
from ytsm.uis.gui_tk.views.channel_browser_view.video_pane import VideoPane, \
    VideoSelection

class AllVideosView(VideoPane):
    """ Frame for All Videos view, inherits BrowserVideoPane and alters VideoSelector for
    AllVideosSelector """
    def __init__(self, master, ytsm_controller):
        super().__init__(master, ytsm_controller, lambda x: None)  # We don't want callback

        # Alter the default pane to change VideoSelector for AllVideosSelector
        self.pane_win.remove(self.video_selection_frame)
        self.video_selection_frame = AllVideosSelection(self, self.ytsm_controller, self.video_detail_box_frame,
                                                        self.callback_video_changes)
        self.pane_win.insert(self.video_detail_box_frame, self.video_selection_frame, weight=10)

class AllVideosSelection(VideoSelection):
    """ Frame for All Videos Selector, reimplements VideoSelector but changes reload_data functionality """
    def reload_data(self, channel_id: str, *, select_video_idx: str = '', selection_activated: bool = True) -> None:
        """
        Reloads video_dto_list and video_treeview
        :param channel_id: channel_id to load Videos for
        :param select_video_idx: id for the currently selected video if we are reloading under selection
        :param selection_activated: call _change_channel_treeview_selection() after reloading
        """
        self.channel_id = channel_id
        [self.video_treeview.delete(i) for i in self.video_treeview.get_children()]  # Delete all contents
        self.video_dto_list = self.ytsm_controller.get_video_dto_list(channel_id, all_videos=True)

        selected_index = 0
        for v_index, v_dto in enumerate(self.video_dto_list):
            content = f'{v_dto.video.sensible_pubdate()} - {v_dto.channel_name} - {v_dto.video.name}'
            tag_type = NEW_VIDEO if v_dto.video.new else UNWATCHED_VIDEO if not v_dto.video.watched else OLD_VIDEO
            self.video_treeview.insert('', END, str(v_index), values=(content,), tags=(tag_type,))
            if v_dto.video.idx == select_video_idx:
                selected_index = v_index

        if self.video_dto_list and selection_activated:
            self.video_treeview.selection_set(str(selected_index))
