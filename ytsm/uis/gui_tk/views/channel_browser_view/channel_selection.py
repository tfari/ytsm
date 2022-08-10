""" Frame for Channel Selection """
from typing import Optional, Callable
from tkinter import BROWSE, END, simpledialog, messagebox, StringVar
from tkinter.ttk import Entry, Button, Frame, Scrollbar, Treeview

from ytsm.uis.ytsm_controller import YTSMController
from ytsm.settings import SETTINGS, NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO


class ChannelSelection(Frame):
    """ Frame for Channel Selection """
    hint_channel_search_str = 'Channel search...'

    def __init__(self, master, ytsm_controller: YTSMController, callback_channel_select: Callable,
                 callback_no_channels: Callable):
        super().__init__(master)
        self.ytsm_controller = ytsm_controller
        self.callback_channel_select = callback_channel_select
        self.callback_no_channels = callback_no_channels
        self.channel_dto_list = []

        self.channel_search_entry_value = StringVar(value=ChannelSelection.hint_channel_search_str)
        self.channel_search_entry = Entry(self, textvariable=self.channel_search_entry_value)

        self.channel_treeview = Treeview(self, columns=('Channel Name',), show='', selectmode=BROWSE)
        self.channel_treeview_scrollbar = Scrollbar(self, command=self.channel_treeview.yview)
        self.channel_treeview.config(yscrollcommand=self.channel_treeview_scrollbar.set)

        self.separator = Frame(self, height=3, style="TFrameSeparator.TFrame")
        self.add_button = Button(self, text='Add', command=self.add_command, underline=0)
        self.remove_button = Button(self, text='Remove', command=self.remove_command, underline=0)
        self.mark_watched_button = Button(self, text='Mark as watched', command=self.mark_watched_command,
                                          underline=0)
        self.update_button = Button(self, text='Update', command=self.update_command, underline=0)
        self.update_all_button = Button(self, text='Update All', command=self.update_all_command, underline=0)
        self.mute_unmute_button = Button(self, text='Mute/Unmute Channel', command=self.mute_unmute_command,
                                         underline=0)
        # Grid
        self.channel_search_entry.grid(column=0, columnspan=6, row=0, sticky='nsew')
        self.channel_treeview.grid(column=0, columnspan=5, row=1, sticky='nsew')
        self.channel_treeview_scrollbar.grid(column=5, row=1, sticky='nsew')

        self.separator.grid(column=0, columnspan=6, row=2, sticky='nsew')
        self.add_button.grid(column=0, columnspan=6, row=3, sticky='nsew')
        self.remove_button.grid(column=0, columnspan=6, row=4, sticky='nsew', pady=2)
        self.mark_watched_button.grid(column=0, columnspan=6, row=5, sticky='nsew')
        self.update_button.grid(column=0, columnspan=6, row=6, sticky='nsew', pady=2)
        self.update_all_button.grid(column=0, columnspan=6, row=7, sticky='nsew')
        self.mute_unmute_button.grid(column=0, columnspan=6, row=8, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=994)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=99)
        self.grid_columnconfigure(1, weight=1)

        # Binding
        self.channel_search_entry_value.trace('w', lambda x, y, z: self._change_channel_search_value())
        self.channel_search_entry.bind('<FocusIn>', lambda x: self._channel_search_entry_has_focus())
        self.channel_search_entry.bind('<FocusOut>', lambda x: self._channel_search_entry_lost_focus())
        self.channel_treeview.bind('<<TreeviewSelect>>', lambda x: self._change_channel_treeview_selection())
        self.channel_treeview.bind('<Return>', lambda x: self._visit_channel_listbox_selection())
        self.channel_treeview.bind('<KP_Enter>', lambda x: self._visit_channel_listbox_selection())

        self.reload_tags()

    def reload_tags(self) -> None:
        """ Load channel_treeview tags """
        tags = {NEW_VIDEO: SETTINGS.gui_settings.colorscheme.foreground_new_video,
                UNWATCHED_VIDEO: SETTINGS.gui_settings.colorscheme.foreground_unwatched_video,
                OLD_VIDEO: SETTINGS.gui_settings.colorscheme.foreground_old_video}
        for t in tags:
            self.channel_treeview.tag_configure(t, foreground=tags[t])

    def focus_set(self) -> None:
        """ Set the focus on self.channel_treeview """
        self.channel_treeview.focus_set()

    def _channel_search_entry_has_focus(self) -> None:
        """ If search_term is a hint, clean the channel_search_entry to accept input """
        search_term = self.channel_search_entry_value.get()
        if search_term == ChannelSelection.hint_channel_search_str:
            self.channel_search_entry.configure(foreground=SETTINGS.gui_settings.colorscheme.foreground)
            self.channel_search_entry_value.set('')

    def _channel_search_entry_lost_focus(self) -> None:
        """ If search_term is empty, write the hint on the channel_search_entry """
        if not self.channel_search_entry_value.get():
            self.channel_search_entry.configure(foreground=SETTINGS.gui_settings.colorscheme.foreground_inactive)
            self.channel_search_entry_value.set(ChannelSelection.hint_channel_search_str)

    def _get_selected_channel_index(self) -> Optional[int]:
        """ Get the index for the currently selected item in self.channel_treeview """
        selection = self.channel_treeview.selection()
        if selection:
            return int(selection[0])
        return None

    def _get_selected_channel_dto(self) -> Optional[YTSMController.ChannelDTO]:
        """ Get ChannelDTO for the currently selected item in self.channel_treeview """
        channel_index = self._get_selected_channel_index()
        if channel_index is not None:
            return self.channel_dto_list[channel_index]
        return None

    def _change_channel_search_value(self) -> None:
        """ Perform a Channel search """
        search_term = self.channel_search_entry_value.get()
        if search_term != ChannelSelection.hint_channel_search_str:
            self.ytsm_controller.set_channel_search_term(search_term)
            self.reload_data()

    def _change_channel_treeview_selection(self) -> None:
        """ channel_treeview selection was changed.
        Call callback_channel_select(ChannelDTO) and reset color tag if channel_dto had new videos. """
        channel_dto = self._get_selected_channel_dto()
        if channel_dto:
            if channel_dto.new:
                self.channel_treeview.item(self.channel_treeview.focus(), tags=UNWATCHED_VIDEO)
            self.callback_channel_select(channel_dto)

    def _visit_channel_listbox_selection(self) -> None:
        """ Visit the Channel selected in channel_treeview """
        channel_dto = self._get_selected_channel_dto()
        if channel_dto:
            self.ytsm_controller.visit_channel(channel_dto.channel.idx)

    def reload_data(self, *, select_channel_idx: str = '', selection_activated: bool = True) -> None:
        """
        Reloads channel_dto_list and channel_treeview
        :param select_channel_idx: id for the currently selected channel if we are reloading under selection
        :param selection_activated: call _change_channel_treeview_selection() after reloading
        """
        [self.channel_treeview.delete(i) for i in self.channel_treeview.get_children()]  # Delete all contents
        self.channel_dto_list = self.ytsm_controller.get_channel_dto_list()

        selected_index = 0  # We will select this index after loading all channel names into the ListBox
        for c_index, c_dto in enumerate(self.channel_dto_list):
            if c_dto.channel.idx == select_channel_idx:  # Check if it is the one we will have to select
                selected_index = c_index
            tag_name = NEW_VIDEO if c_dto.new else UNWATCHED_VIDEO if c_dto.unwatched else OLD_VIDEO
            muted = '(m) ' if not c_dto.channel.notify_on else ''
            display_text = f'{muted}{c_dto.channel.name}'
            self.channel_treeview.insert('', END, str(c_index), values=(display_text,), tags=(tag_name,))

        if self.channel_dto_list and selection_activated:
            self.channel_treeview.selection_set(str(selected_index))
        elif not self.channel_dto_list:
            self.callback_no_channels()

    def add_command(self) -> None:
        """ Add a new Channel """
        url = simpledialog.askstring(f'Add Channel', f'Input YT url (/watch, /channel, /c, /user):', parent=self)
        if url:
            try:
                new_c = self.ytsm_controller.add_channel(url)
            except YTSMController.AddChannelError as e:
                messagebox.showerror('Add Channel Failed!', f'{str(e)}')
            else:
                messagebox.showinfo('Added Channel', f'Channel "{new_c.name}" was successfully added!')
                self.reload_data(select_channel_idx=new_c.idx)

    def remove_command(self) -> None:
        """ Remove a Channel """
        channel_dto = self._get_selected_channel_dto()
        if channel_dto:
            confirm = messagebox.askyesno(f'Remove Channel', f'Remove channel: "{channel_dto.channel.name}"')
            if confirm:
                self.ytsm_controller.remove_channel(channel_dto)
                messagebox.showinfo('Removed Channel', f'"{channel_dto.channel.name}" was successfully removed.')
                self.reload_data()

    def mark_watched_command(self) -> None:
        """ Mark all videos in a Channel as watched """
        channel_dto = self._get_selected_channel_dto()
        if channel_dto:
            self.ytsm_controller.mark_channel_all_watched(channel_dto)
            self.reload_data(select_channel_idx=channel_dto.channel.idx)

    def update_command(self) -> None:
        """ Update a Channel """
        channel_dto = self._get_selected_channel_dto()
        if channel_dto:
            try:
                amt = self.ytsm_controller.update_channel(channel_dto)
                messagebox.showinfo('Updated Channel', f'"{channel_dto.channel.name}" updated: {amt} new videos.')
                self.reload_data(select_channel_idx=channel_dto.channel.idx)
            except YTSMController.UpdateChannelError as e:
                messagebox.showerror('Update Channel Failed!', f'{str(e)}')

    def update_all_command(self) -> None:
        """ Update all Channels """
        try:
            update_data = self.ytsm_controller.update_all_channels()
        except YTSMController.UpdateAllChannelsError as e:
            messagebox.showerror('Update All Channels Failed!', f'{str(e)}')
        else:
            amt = update_data['total']
            cns = ", ".join([f'"{ud[0]}"' for ud in update_data['details']])
            messagebox.showinfo('Updated all Channels', f'All channels updated:\n {amt} total new videos in Channels:'
                                                        f' {cns}')
            self.reload_data()

    def mute_unmute_command(self) -> None:
        """ Mute / unmute a Channel """
        channel_dto = self._get_selected_channel_dto()
        if channel_dto:
            self.ytsm_controller.toggle_mute_channel(channel_dto)
        self.reload_data(select_channel_idx=channel_dto.channel.idx)
