""" Frame for Video Detail Information """
import threading
from typing import Callable

from tkinter import StringVar, Text, LEFT, END, NORMAL, DISABLED, FLAT
from tkinter.ttk import Frame, Label, Scrollbar, Button

from ytsm.uis.ytsm_controller import YTSMController
from ytsm.uis.gui_tk.images_handler import IMAGES_HANDLER

from ytsm.settings import SETTINGS


class VideoDetailBox(Frame):
    """ Frame for Video Detail Information """
    def __init__(self, master, ytsm_controller: YTSMController, callback_video_alterations: Callable,
                 video_dto: YTSMController.VideoDTO = None):
        super().__init__(master)
        self.ytsm_controller = ytsm_controller
        self.callback_video_alterations = callback_video_alterations
        self.video_dto = video_dto

        self.ih = IMAGES_HANDLER
        self.ih.instantiate_default_images()

        # Widgets
        self.video_title_text = StringVar()
        self.video_title = Label(self, textvariable=self.video_title_text, justify=LEFT, anchor='nw',
                                 style='TBigLabel.TLabel')

        self.video_date_text = StringVar()
        self.video_date = Label(self, textvariable=self.video_date_text, justify=LEFT, anchor='nw',
                                style='TSmallLabel.TLabel')
        self.video_image_label = Label(self, image=None)
        self.video_image_label.image = None
        self.channel_image_label = Label(self, image=None)
        self.channel_image_label.image = None

        self.video_desc_text = Text(self, height=10, state=DISABLED)
        self.video_desc_text_scrollbar = Scrollbar(self, command=self.video_desc_text.yview)
        self.video_desc_text.config(yscrollcommand=self.video_desc_text_scrollbar.set)
        self.video_desc_text.configure(relief=FLAT,
                                       background=SETTINGS.gui_settings.colorscheme.background,
                                       borderwidth=0,
                                       highlightbackground=SETTINGS.gui_settings.colorscheme.background,
                                       highlightcolor=SETTINGS.gui_settings.colorscheme.background,
                                       foreground=SETTINGS.gui_settings.colorscheme.foreground_inactive)

        # Buttons
        self.buttons_frame = Frame(self)
        self.watch_video_button = Button(self.buttons_frame, text='Watch Video',
                                         command=self.watch_video_command, underline=0)
        self.mark_video_watched_button = Button(self.buttons_frame, text='Mark Video Watched',
                                                command=self.mark_video_watched_command, underline=0)
        self.visit_channel_button = Button(self.buttons_frame, text='Visit Channel',
                                           command=self.visit_channel_command, underline=0)

        # Grids
        self.channel_image_label.grid(column=0, row=0, columnspan=1, rowspan=2, sticky='nsew', padx=5, pady=(4, 0))
        self.video_title.grid(column=1, row=0, columnspan=6, sticky='nsew', padx=5)
        self.video_date.grid(column=1, row=1, columnspan=6, sticky='nsew', padx=5)
        self.video_desc_text.grid(column=0, row=2, columnspan=2, sticky='nsew', padx=5)
        self.video_image_label.grid(column=3, row=2, sticky='nsew', padx=(0, 0))
        self.video_desc_text_scrollbar.grid(column=4, row=2, sticky='nsew')
        self.buttons_frame.grid(column=0, columnspan=5, row=3, sticky='nsew')

        self.watch_video_button.grid(column=0, row=0, sticky='nsew')
        self.visit_channel_button.grid(column=1, row=0, sticky='nsew')
        self.mark_video_watched_button.grid(column=2, row=0, sticky='nsew')
        self.buttons_frame.grid_columnconfigure(0, weight=2)
        self.buttons_frame.grid_columnconfigure(1, weight=2)
        self.buttons_frame.grid_columnconfigure(2, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=100)
        self.grid_rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

    def clear_detail(self) -> None:
        """ Clear displayed Video detail information """
        self.video_dto = None
        self.video_title_text.set('')
        self.video_date_text.set('')
        self.video_desc_text.configure(state=NORMAL)
        self.video_desc_text.delete("0.0", END)
        self.video_desc_text.configure(state=DISABLED)

        self.video_image_label.configure(image='')
        self.channel_image_label.configure(image='')

    def change_details(self, video_dto: YTSMController.VideoDTO) -> None:
        """ Change displayed Video detail information """
        previous_channel_id = self.video_dto.video.channel_id if self.video_dto else None  # Save the last Channel's id

        # Set texts
        self.video_dto = video_dto
        self.video_title_text.set(self.video_dto.video.name)
        self.video_date_text.set(self.video_dto.video.sensible_pubdate() + ' - ' + self.video_dto.channel_name)
        self.video_desc_text.configure(state=NORMAL)
        self.video_desc_text.delete("0.0", END)
        self.video_desc_text.insert(END, self.video_dto.video.description)
        self.video_desc_text.configure(foreground=SETTINGS.gui_settings.colorscheme.foreground_inactive)
        self.video_desc_text.configure(state=DISABLED)

        # Get Video's thumbnail on a separate thread
        t1 = threading.Thread(target=self.ih.video_thumbnail_get, args=(self.video_dto,))
        t1.start()
        self.after(100, self._thumbnail_draw, video_dto.video.idx, self.ih.video_img_cache, self.video_image_label)

        # If the channel_id is different from the previous_channel_id, or the cached channel is the default one,
        # get Channel's thumbnail on a separate thread
        if previous_channel_id != self.video_dto.video.channel_id or self.ih.get_id_in_cache(
                self.video_dto.video.channel_id, self.ih.channel_img_cache) == self.ih.default_channel_image:
            try:  # Check channel exists!
                channel_dto = self.ytsm_controller.get_channel_dto_from_id(self.video_dto.video.channel_id)
            except YTSMController.ChannelIDNotFound as e:
                raise NotImplementedError(e)  # TODO
            else:
                t2 = threading.Thread(target=self.ih.channel_thumbnail_get, args=(channel_dto,))
                t2.start()
                self.after(100, self._thumbnail_draw, channel_dto.channel.idx, self.ih.channel_img_cache,
                           self.channel_image_label)

    def _thumbnail_draw(self, object_id: str, using_cache: dict, image_label) -> None:
        """ Draw a thumbnail img from self.ih using_cache cache, into the image_label"""
        # If object_id is not in the using_cache, we call ourselves and wait, if its there, and is different from
        # the current image, we draw it.
        if self.ih.id_in_cache(object_id, using_cache):
            img = self.ih.get_id_in_cache(object_id, using_cache)
            if image_label.image != img:
                image_label.configure(image=img)
                image_label.image = img
        else:
            self.after(100, self._thumbnail_draw, object_id, using_cache, image_label)

    def visit_channel_command(self) -> None:
        """ Visit the Channel associated with the VideoDTO """
        if self.video_dto:
            try:
                channel_dto = self.ytsm_controller.get_channel_dto_from_id(self.video_dto.video.channel_id)
                self.ytsm_controller.visit_channel(channel_dto)
            except YTSMController.ChannelIDNotFound as e:
                raise NotImplementedError(e)  # TODO

    def watch_video_command(self) -> None:
        """ Watch the Video associated with the VideoDTO """
        if self.video_dto:
            self.ytsm_controller.watch_video(self.video_dto)
            self.callback_video_alterations(self.video_dto)

    def mark_video_watched_command(self) -> None:
        """ Mark the Video associated with the VideoDTO as watched """
        if self.video_dto:
            self.ytsm_controller.mark_video_watched(self.video_dto)
            self.callback_video_alterations(self.video_dto)
