""" Frames for Video Pane, Video Selection, and Video Details """
from __future__ import annotations

from tkinter import VERTICAL
from tkinter.ttk import Frame, Panedwindow
from typing import Callable

from ytsm.uis.gui_tk.views.channel_browser_view.video_selection import VideoSelection
from ytsm.uis.gui_tk.views.video_detailbox import VideoDetailBox
from ytsm.uis.ytsm_controller import YTSMController


class VideoPane(Frame):
    """ Frame for Video Pane """
    def __init__(self, master, ytsm_controller: YTSMController, callback_video_alterations: Callable):
        super().__init__(master)
        self.ytsm_controller = ytsm_controller
        self.callback_video_alterations = callback_video_alterations

        self.pane_win = Panedwindow(self, orient=VERTICAL)
        self.video_detail_box_frame = VideoDetailBox(self.pane_win, self.ytsm_controller,
                                                     self.callback_video_changes)
        self.video_selection_frame = VideoSelection(self.pane_win, self.ytsm_controller,
                                                    self.video_detail_box_frame,
                                                    self.callback_video_changes)

        self.pane_win.add(self.video_selection_frame, weight=1)
        self.pane_win.add(self.video_detail_box_frame, weight=1)

        # Grid
        self.pane_win.grid(column=0, row=0, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def tab_enter(self) -> None:
        """ Tab has been entered."""
        self.video_selection_frame.tab_enter()

    def no_channels(self):
        """ There are no Channels in the Channel Selection pane """
        self.video_selection_frame.no_channels()

    def channel_selection_changed(self, channel_dto: YTSMController.ChannelDTO) -> None:
        """ Channel selection changed """
        self.video_selection_frame.reload_data(channel_dto.channel.idx, selection_activated=False)

    def callback_video_changes(self, video_dto: YTSMController.VideoDTO) -> None:
        """ Callback for Video alterations action """
        self.video_selection_frame.reload_data(video_dto.video.channel_id, select_video_idx=video_dto.video.idx)
        self.callback_video_alterations(video_dto)
