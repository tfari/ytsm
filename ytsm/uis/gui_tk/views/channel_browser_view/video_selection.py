""" Frame for Video Selection """
from typing import Callable, Optional
from tkinter import StringVar, FLAT, END
from tkinter.ttk import Entry, Frame, OptionMenu, Treeview, Scrollbar

from ytsm.uis.gui_tk.views.video_detailbox import VideoDetailBox

from ytsm.uis.ytsm_controller import YTSMController
from ytsm.settings import SETTINGS, NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO

class VideoSelection(Frame):
    """ Frame for Video Selection """
    class VideoSearchFrame(Frame):
        """ Frame for Video Search controls """
        hint_video_search_str = 'Video search...'

        def __init__(self, master):
            super().__init__(master)
            self.video_search_entry_value = StringVar(value=VideoSelection.VideoSearchFrame.hint_video_search_str)
            self.video_search_entry = Entry(self, textvariable=self.video_search_entry_value)
            self.video_search_select_value = StringVar()
            self.video_search_select_value.set('Name')
            self.video_search_select = OptionMenu(self, self.video_search_select_value, 'Name',
                                                  *('Name', 'Desc', 'Date'))
            self.video_filter_select_value = StringVar()
            self.video_filter_select_value.set('All')
            self.video_filter_select = OptionMenu(self, self.video_filter_select_value, 'All',
                                                  *('All', 'New', 'Unwatched'))

            # Menu Styling
            option_menus = [self.video_search_select, self.video_filter_select]
            for om in option_menus:
                om['menu'].config(
                    activebackground=SETTINGS.gui_settings.colorscheme.background_active,
                    background=SETTINGS.gui_settings.colorscheme.background,
                    activeborderwidth=0,
                    borderwidth=0,
                    relief=FLAT,
                    selectcolor=SETTINGS.gui_settings.colorscheme.accent,
                    activeforeground=SETTINGS.gui_settings.colorscheme.foreground,
                    foreground=SETTINGS.gui_settings.colorscheme.foreground)

            # Grid
            self.video_search_entry.grid(column=0, row=0, sticky='nsew')
            self.video_search_select.grid(column=1, row=0, sticky='nsew')
            self.video_filter_select.grid(column=2, row=0, sticky='nsew')
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=100)
            self.grid_columnconfigure(1, weight=1)
            self.grid_columnconfigure(2, weight=1)

    def __init__(self, master, ytsm_controller: YTSMController, video_detail: VideoDetailBox,
                 callback_video_alterations: Callable):
        super().__init__(master)
        self.ytsm_controller = ytsm_controller
        self.video_detail = video_detail
        self.callback_video_alterations = callback_video_alterations

        self.video_dto_list = []
        self.channel_id = ''

        self.video_search_frame = VideoSelection.VideoSearchFrame(self)
        self.video_treeview = Treeview(self, columns=('Video Name',), show='')
        self.video_treeview_scrollbar = Scrollbar(self, command=self.video_treeview.yview)
        self.video_treeview.config(yscrollcommand=self.video_treeview_scrollbar.set)

        # Grid
        self.video_search_frame.grid(column=0, row=0, columnspan=6, sticky='nsew')
        self.video_treeview.grid(column=0, columnspan=5, row=1, sticky='nsew')
        self.video_treeview_scrollbar.grid(column=5, row=1, sticky='nsew')

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=999)
        self.grid_columnconfigure(0, weight=100)
        self.grid_columnconfigure(4, weight=1)

        # Bindings
        self.video_search_frame.video_filter_select_value.trace('w', lambda x, y, z: self._change_video_filter())
        self.video_search_frame.video_search_select_value.trace('w', lambda x, y, z: self._change_video_search_type())
        self.video_search_frame.video_search_entry_value.trace('w', lambda x, y, z: self._change_video_search_terms())
        self.video_search_frame.video_search_entry.bind('<FocusIn>', lambda x: self._video_search_entry_has_focus())
        self.video_search_frame.video_search_entry.bind('<FocusOut>', lambda x: self._video_search_entry_lost_focus())

        self.video_treeview.bind('<<TreeviewSelect>>', lambda x: self._change_video_listbox_selection())
        self.video_treeview.bind('<Return>', lambda x: self._watch_video_listbox_selection())
        self.video_treeview.bind('<KP_Enter>', lambda x: self._watch_video_listbox_selection())

        self.reload_tags()

    def reload_tags(self) -> None:
        """ Load video_treeview tags """
        tags = {NEW_VIDEO: SETTINGS.gui_settings.colorscheme.foreground_new_video,
                UNWATCHED_VIDEO: SETTINGS.gui_settings.colorscheme.foreground_unwatched_video,
                OLD_VIDEO: SETTINGS.gui_settings.colorscheme.foreground_old_video}
        for t in tags:
            self.video_treeview.tag_configure(t, foreground=tags[t])

    def _video_search_entry_has_focus(self) -> None:
        """ If search_term is a hint, clean the video_search_entry to accept input """
        search_term = self.video_search_frame.video_search_entry_value.get()
        if search_term == VideoSelection.VideoSearchFrame.hint_video_search_str:
            self.video_search_frame.video_search_entry.configure(
                foreground=SETTINGS.gui_settings.colorscheme.foreground)
            self.video_search_frame.video_search_entry_value.set('')

    def _video_search_entry_lost_focus(self) -> None:
        """ If search_term is empty, write the hint on the video_search_entry """
        if not self.video_search_frame.video_search_entry_value.get():
            self.video_search_frame.video_search_entry.configure(
                foreground=SETTINGS.gui_settings.colorscheme.foreground_inactive)
            self.video_search_frame.video_search_entry_value.set(
                VideoSelection.VideoSearchFrame.hint_video_search_str)

    def _get_selected_video_index(self) -> Optional[int]:
        """ Get the index for the currently selected item in self.video_treeview """
        selection = self.video_treeview.selection()
        if selection:
            return int(selection[0])
        return None

    def _get_selected_video_dto(self) -> Optional[YTSMController.VideoDTO]:
        """ Get VideoDTO for the currently selected item in self.video_treeview """
        video_index = self._get_selected_video_index()
        if video_index is not None:
            return self.video_dto_list[video_index]
        return None

    def _change_video_filter(self, call_reload_data: bool = True) -> None:
        """
        Change the video filter
        :param call_reload_data: Call reload_data
        """
        self.ytsm_controller.set_video_filter(self.video_search_frame.video_filter_select_value.get().upper())
        if call_reload_data:
            self.reload_data(self.channel_id)

    def _change_video_search_type(self) -> None:
        """ Change the video search type """
        self.ytsm_controller.set_video_search_type(self.video_search_frame.video_search_select_value.get().upper())
        self._change_video_search_terms()

    def _change_video_search_terms(self) -> None:
        """ Perform a Video search """
        search_term = self.video_search_frame.video_search_entry.get()
        if search_term != VideoSelection.VideoSearchFrame.hint_video_search_str:
            self.ytsm_controller.set_video_search_term(search_term)
        else:
            self.ytsm_controller.set_video_search_term('')
        self.reload_data(self.channel_id)

    def tab_enter(self) -> None:
        """ Tab has been entered. Reload filters and search terms. """
        self._change_video_filter(call_reload_data=False)
        self._change_video_search_type()

    def _change_video_listbox_selection(self) -> None:
        """ video_treeview selection was changed. Alter the VideoDetailBox information. """
        video_dto = self._get_selected_video_dto()
        if video_dto:
            self.video_detail.change_details(video_dto)
        else:
            if not self.video_dto_list:
                self.video_detail.clear_detail()

    def _watch_video_listbox_selection(self) -> None:
        """ Watch the video selected on video_treeview """
        self.video_detail.watch_video_command()

    def reload_data(self, channel_id: str, *, select_video_idx: str = '', selection_activated: bool = True) -> None:
        """
        Reloads video_dto_list and video_treeview
        :param channel_id: channel_id to load Videos for
        :param select_video_idx: id for the currently selected video if we are reloading under selection
        :param selection_activated: call _change_channel_treeview_selection() after reloading
        """
        self.channel_id = channel_id
        [self.video_treeview.delete(i) for i in self.video_treeview.get_children()]  # Delete all contents
        self.video_dto_list = self.ytsm_controller.get_video_dto_list(channel_id)

        selected_index = 0
        for v_index, v_dto in enumerate(self.video_dto_list):
            content = f'{v_dto.video.name}'
            tag_type = NEW_VIDEO if v_dto.video.new else UNWATCHED_VIDEO if not v_dto.video.watched else OLD_VIDEO
            self.video_treeview.insert('', END, str(v_index), values=(content,), tags=(tag_type,))
            if v_dto.video.idx == select_video_idx:
                selected_index = v_index

        if self.video_dto_list and selection_activated:
            self.video_treeview.selection_set(str(selected_index))
        elif self.video_dto_list:
            self.video_detail.change_details(self.video_dto_list[selected_index])
        else:
            self.video_detail.clear_detail()

    def no_channels(self):
        """ There are no Channels in the Channel Selection pane """
        self.channel_id = None
        [self.video_treeview.delete(i) for i in self.video_treeview.get_children()]  # Delete all contents
        self.video_detail.ih.clear_caches()
        self.video_detail.clear_detail()
