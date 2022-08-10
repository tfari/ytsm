""" About View """
import webbrowser
from tkinter import Text, FLAT, DISABLED, END, WORD
from tkinter.ttk import Frame, Label, Button, Scrollbar

from ytsm.settings import SETTINGS

class AboutView(Frame):
    """ Displays app information """
    ABOUT_STR = 'YTSM is a YT Subscription manager. Add, remove, and update any channels you want to follow; watch ' \
                'and keep a log of the videos you have watched. \n\nYTSM uses YT\'s RSS feeds, which return ' \
                'information ' \
                'of the newest 15 videos of a Channel, to maintain a local database of videos, by saving the ' \
                'last 100 ' \
                'videos for each Channel. The video information can be updated by channel, or all at the same time, ' \
                'once can also get real-time notifications on updates by using the command "notify-update", ' \
                'which calls an update on all Channels, and then utilizes the "notify-send" ' \
                '(https://vaskovsky.net/notify-send/) tool to access the system\'s notification tray. You can ' \
                'schedule the call of this command via something like cron, as well as keeping any Channels muted, ' \
                'if you don\'t want to receive notifications for any specific ones.\n\nYTSM provides cli, tui, ' \
                'and gui frontends to access, filter, search, and modify the data, as well as launch the videos in ' \
                'your default browser. The three can be configured via the settings.json file in the data folder, ' \
                'or via the GUI.\n\nWhen searching for videos by date, the format the program understands is ' \
                '"YYYY-MM-DD YYYY-MM-DD", where the first date is the lower range, and the second date the max range.'

    def __init__(self, master):
        super().__init__(master)
        self.about_label = Label(self, text='About YTSM', style='TBigLabel.TLabel')
        self.about_text_frame = Frame(self)
        self.visit_repo_button = Button(self, text='Visit repository', underline=0, command=self.visit_repository)
        self.about_text = Text(self, height=10, wrap=WORD)
        self.about_text.insert(END, AboutView.ABOUT_STR)
        self.about_text.configure(state=DISABLED)
        self.about_text_scrollbar = Scrollbar(self, command=self.about_text.yview)
        self.about_text.config(yscrollcommand=self.about_text_scrollbar.set)
        self.about_text.configure(relief=FLAT,
                                       background=SETTINGS.gui_settings.colorscheme.background,
                                       borderwidth=0,
                                       highlightbackground=SETTINGS.gui_settings.colorscheme.background,
                                       highlightcolor=SETTINGS.gui_settings.colorscheme.background,
                                       foreground=SETTINGS.gui_settings.colorscheme.foreground_inactive)

        # Grid
        self.about_label.grid(row=0, column=0, pady=10, sticky='ns')
        self.about_text.grid(row=1, column=0, sticky='nsew', padx=10)
        self.about_text_scrollbar.grid(row=1, column=1, sticky='nsew')
        self.visit_repo_button.grid(row=2, column=0, sticky='nsew')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=99)
        self.rowconfigure(2, weight=1)

    @staticmethod
    def visit_repository() -> None:
        """ Open YTSM repository in the webbrowser """
        webbrowser.open('https://github.com/tfari/ytsm')
