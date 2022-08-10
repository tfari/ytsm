""" Frame for ChannelBrowser window """
from tkinter import HORIZONTAL
from tkinter.ttk import Frame, Panedwindow

from ytsm.uis.gui_tk.views.channel_browser_view.video_pane import VideoPane
from ytsm.uis.gui_tk.views.channel_browser_view.channel_selection import ChannelSelection
from ytsm.uis.ytsm_controller import YTSMController


class ChannelBrowserView(Frame):
    """ Frame for ChannelBrowser view """
    def __init__(self, master, ytsm_controller: YTSMController):
        super().__init__(master)
        self.ytsm_controller = ytsm_controller

        self.pane_win = Panedwindow(self, orient=HORIZONTAL)
        self.channel_selection_pane = ChannelSelection(self.pane_win, self.ytsm_controller,
                                                       self.callback_channel_selection,
                                                       self.callback_no_channels)
        self.video_selection_pane = VideoPane(self.pane_win, self.ytsm_controller,
                                              self.callback_video_alterations)
        self.pane_win.add(self.channel_selection_pane)
        self.pane_win.add(self.video_selection_pane)

        self.pane_win.grid(column=0, row=0, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def callback_channel_selection(self, channel_dto: YTSMController.ChannelDTO) -> None:
        """ Callback for Channel selection action """
        self.video_selection_pane.channel_selection_changed(channel_dto)

    def callback_video_alterations(self, video_dto: YTSMController.VideoDTO) -> None:
        """ Callback for Video alterations action """
        self.channel_selection_pane.reload_data(select_channel_idx=video_dto.video.channel_id,
                                                selection_activated=False)

    def callback_no_channels(self) -> None:
        """ Callback for when there are no Channels in the channel pane """
        self.video_selection_pane.no_channels()

    def tab_enter(self) -> None:
        """ Tab has been entered """
        self.video_selection_pane.tab_enter()
