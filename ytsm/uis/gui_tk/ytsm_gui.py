""" Tkinter based GUI """
from tkinter import Tk, FLAT, messagebox, DISABLED
from tkinter.font import Font
from tkinter.ttk import Style, Notebook, Progressbar

from ytsm.ytsubmanager import YTSubManager
from ytsm.uis.ytsm_controller import YTSMController
from ytsm.uis.gui_tk.views.all_videos_view import AllVideosView
from ytsm.uis.gui_tk.views.channel_browser_view.channel_browser_view import ChannelBrowserView
from ytsm.uis.gui_tk.views.settings_window.settings_window import SettingsView
from ytsm.uis.gui_tk.views.about_view import AboutView

from ytsm.settings import SETTINGS


class YTSMGUI(Tk):
    """ Root GUI widget """
    def __init__(self, ytsm: YTSubManager):
        super().__init__()
        self.ytsm_controller = YTSMController(ytsm)

        # Styling
        self.style = Style()
        self.normal_font = None
        self.small_font = None
        self.medium_font = None
        self.big_font = None
        self.title("YTSM")

        self.reload_styles(reload_tags=False)

        # Set image caches
        self.cache_channel_images = {}
        self.cache_video_images = {}

        # Set main notebook
        self.main_window = Notebook(self, padding=(10, 10))
        self.main_window.enable_traversal()
        self.channel_browser_view = ChannelBrowserView(self.main_window, self.ytsm_controller)
        self.all_videos_view = AllVideosView(self.main_window, self.ytsm_controller)
        self.settings_view = SettingsView(self.main_window, self.reload_styles)
        # self.about_view = AboutView(self.main_window)

        self.main_window.add(self.channel_browser_view, text='Channel Browser', underline=0)
        self.main_window.add(self.all_videos_view, text='All Videos', underline=0)
        self.main_window.add(self.settings_view, text='Settings', underline=0)
        # self.main_window.add(self.about_view, text='About', underline=0)

        # Set progressbar
        self.progress_bar = Progressbar(self, mode='determinate')

        # Grid
        self.main_window.grid(column=0, row=0, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # Set up
        self.main_window.bind('<<NotebookTabChanged>>', lambda x: self.enter_tab_reload())
        self.all_videos_view.video_selection_frame.reload_data('')
        self.channel_browser_view.channel_selection_pane.reload_data()
        self.channel_browser_view.channel_selection_pane.focus_set()
        self.scheduled_update_caller(first_run=True)
        self.mainloop()

    def enter_tab_reload(self):
        """ Call enter_tab on the channel_browser and all_videos tabs, so that they reload the search terms. """
        frame_index = self.main_window.index(self.main_window.select())
        if frame_index == 0:
            self.channel_browser_view.tab_enter()
        elif frame_index == 1:
            self.all_videos_view.tab_enter()

    def scheduled_update_caller(self, first_run: bool = False) -> None:
        """
        Schedule update loop.
        Loop every X minutes, if activated, edit the title, show and activate the progressbar,
        and call self.call_update_all_channels.

        :param first_run: Only used on YTSMGUI instantiation, so that updating does not occur when opening app,
        to prevent freeze when opening.
        """
        if SETTINGS.gui_settings.scheduled_update_activated and not first_run:
            self.progress_bar.grid(row=1, column=0, sticky='nsew')
            self.title('YTSM - Updating all channels...')
            # For show, we assume update_all_channels will take ~2/3 secs, the bar will indicate the freeze is normal
            self.progress_bar.start(interval=10)
            self.after(1000, self.call_update_all_channels)
        self.after(((SETTINGS.gui_settings.scheduled_update_minutes * 60) * 1000), self.scheduled_update_caller)

    def call_update_all_channels(self) -> None:
        """
        Call an update for all channels.
        After updating fix the title, stop and hide the progressbar, and open a messagebox if there are new videos.
        """
        try:
            update_data = self.ytsm_controller.update_all_channels()
        except YTSMController.UpdateAllChannelsError as e:
            messagebox.showerror('Update All Channels Failed!', f'{str(e)}')
        else:
            # Display, if new videos
            if update_data['total'] > 0:
                amt = update_data['total']
                cns = ", ".join([f'"{ud[0]}"' for ud in update_data['details']])
                messagebox.showinfo('Updated all Channels',
                                    f'All channels updated:\n {amt} total new videos in Channels:'
                                    f' {cns}')
                notebook_index = self.main_window.index(self.main_window.select())
                if notebook_index == 0 or notebook_index == 1:
                    self.channel_browser_view.channel_selection_pane.reload_data(selection_activated=False)
                    self.all_videos_view.video_selection_frame.reload_data('')

        # Clean
        self.title("YTSM")
        self.progress_bar.stop()
        self.progress_bar.grid_remove()

    def reload_styles(self, reload_tags: bool = True) -> None:
        """ 
        Reload styling

        :param reload_tags: If this is true, reload tags as well. (Only false in YTSMGUI instantiation, as there is
        nothing to reload yet).
        """
        self.attributes('-topmost', SETTINGS.gui_settings.window_on_top)
        self.geometry(f'{SETTINGS.gui_settings.default_window_size[0]}x{SETTINGS.gui_settings.default_window_size[1]}')

        self.normal_font = Font(family=SETTINGS.gui_settings.fontscheme.family_name,
                                size=SETTINGS.gui_settings.fontscheme.normal_size)
        self.small_font = Font(family=SETTINGS.gui_settings.fontscheme.family_name,
                               size=SETTINGS.gui_settings.fontscheme.small_size)
        self.medium_font = Font(family=SETTINGS.gui_settings.fontscheme.family_name,
                                size=SETTINGS.gui_settings.fontscheme.medium_size)
        self.big_font = Font(family=SETTINGS.gui_settings.fontscheme.family_name,
                             size=SETTINGS.gui_settings.fontscheme.big_size)

        self.style.configure('.', background=SETTINGS.gui_settings.colorscheme.background,
                             foreground=SETTINGS.gui_settings.colorscheme.foreground,
                             font=self.normal_font)
        self.style.map('.', background=[("active", SETTINGS.gui_settings.colorscheme.background_active),
                                        ("pressed", SETTINGS.gui_settings.colorscheme.accent)])

        # TFrameSeparator
        self.style.configure('TFrameSeparator.TFrame', background=SETTINGS.gui_settings.colorscheme.background_darker)

        # TNotebook
        self.style.configure('TNotebook', borderwidth=0, background=SETTINGS.gui_settings.colorscheme.background_darker,
                             relief=FLAT)

        self.style.configure('TNotebook.Tab',
                             background=SETTINGS.gui_settings.colorscheme.background_darker,
                             borderwidth=0,
                             padding=[3, 2, 40, 2],
                             font=self.medium_font)
        self.style.map('TNotebook.Tab', background=[("selected", SETTINGS.gui_settings.colorscheme.background),
                                                    ("active", SETTINGS.gui_settings.colorscheme.background_active)])
        # TWindowpane
        self.style.configure('TPanedwindow', background=SETTINGS.gui_settings.colorscheme.background_darker)

        # TEntry
        self.style.configure('TEntry',
                             background="red",
                             foreground=SETTINGS.gui_settings.colorscheme.foreground_inactive,
                             fieldbackground=SETTINGS.gui_settings.colorscheme.entry_box_inactive,
                             selectbackground=SETTINGS.gui_settings.colorscheme.accent,
                             insertcolor=SETTINGS.gui_settings.colorscheme.foreground,
                             borderwidth=0,
                             padding=(5, 3),
                             )
        self.style.map('TEntry', fieldbackground=[("focus", SETTINGS.gui_settings.colorscheme.entry_box_active)])

        # TTreeView
        self.style.configure('Treeview',
                             background=SETTINGS.gui_settings.colorscheme.background,
                             borderwidth=0,
                             fieldbackground=SETTINGS.gui_settings.colorscheme.background)
        self.style.map('Treeview', background=[("selected", SETTINGS.gui_settings.colorscheme.accent)])
        # Settings Treeview
        self.style.configure('TSettingsTreeview.Treeview',
                             background=SETTINGS.gui_settings.colorscheme.entry_box_inactive)

        # TScrollBar
        self.style.configure('Vertical.TScrollbar',
                             relief=FLAT,
                             borderwidth=0,
                             background=SETTINGS.gui_settings.colorscheme.background,
                             arrowcolor=SETTINGS.gui_settings.colorscheme.background,
                             troughcolor=SETTINGS.gui_settings.colorscheme.accent,
                             )
        self.style.map('Vertical.TScrollbar',
                       background=[("active", SETTINGS.gui_settings.colorscheme.background),
                                   ("disabled", SETTINGS.gui_settings.colorscheme.background)],
                       arrowcolor=[("active", SETTINGS.gui_settings.colorscheme.background),
                                   ("disabled", SETTINGS.gui_settings.colorscheme.background)])

        # TButton
        self.style.configure('TButton', relief=FLAT, font=self.medium_font)
        self.style.map('TButton', relief=[("active", FLAT)],
                       background=[("pressed", SETTINGS.gui_settings.colorscheme.accent),
                                   ("active", SETTINGS.gui_settings.colorscheme.background_active)])
        # TLabels
        self.style.configure('TBigLabel.TLabel', font=self.big_font)
        self.style.configure('TMediumLabel.TLabel', font=self.medium_font)
        self.style.configure('TSmallLabel.TLabel', font=self.small_font)

        # TOptionMenu
        self.style.configure('TMenubutton', relief=FLAT, borderwidth=0, font=self.medium_font)

        # TSpinbox
        self.style.configure('TSpinbox',
                             foreground=SETTINGS.gui_settings.colorscheme.foreground,
                             arrowcolor=SETTINGS.gui_settings.colorscheme.accent,
                             fieldbackground=SETTINGS.gui_settings.colorscheme.entry_box_inactive,
                             selectbackground=SETTINGS.gui_settings.colorscheme.accent,
                             bordercolor=SETTINGS.gui_settings.colorscheme.entry_box_inactive,
                             borderwidth=0,
                             arrowsize=13,
                             insertcolor=SETTINGS.gui_settings.colorscheme.accent,
                             relief=FLAT)
        self.style.map('TSpinbox', fieldbackground=[("focus", SETTINGS.gui_settings.colorscheme.entry_box_active)])

        # TCheckButton
        self.style.configure('TCheckbutton',
                             font=self.normal_font,
                             foreground=SETTINGS.gui_settings.colorscheme.foreground,
                             indicatorcolor=SETTINGS.gui_settings.colorscheme.background,
                             background=SETTINGS.gui_settings.colorscheme.background)
        self.style.map('TCheckbutton',
                       indicatorcolor=[("selected", SETTINGS.gui_settings.colorscheme.accent)])

        # TProgressbar
        self.style.configure('TProgressbar',
                             background=SETTINGS.gui_settings.colorscheme.accent,
                             troughcolor=SETTINGS.gui_settings.colorscheme.background_darker,
                             bordercolor=SETTINGS.gui_settings.colorscheme.background_darker,
                             darkcolor=SETTINGS.gui_settings.colorscheme.background_darker,
                             lightcolor=SETTINGS.gui_settings.colorscheme.background_darker,
                             troughrelief=FLAT,
                             borderwidth=0)

        # Edit globals for simpledialog
        self.option_add('*background', SETTINGS.gui_settings.colorscheme.background)
        self.option_add('*foreground', SETTINGS.gui_settings.colorscheme.foreground)
        self.option_add('*Entry*background', SETTINGS.gui_settings.colorscheme.entry_box_active)
        self.option_add('*Button*relief', FLAT)

        self.configure({'bg': SETTINGS.gui_settings.colorscheme.background_darker})

        # Reload
        if reload_tags:
            self.channel_browser_view.channel_selection_pane.reload_tags()
            self.channel_browser_view.video_selection_pane.video_selection_frame.reload_tags()
            self.all_videos_view.video_selection_frame.reload_tags()
