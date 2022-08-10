""" Frames for Settings window, GUISettings """
from typing import Callable
from tkinter.ttk import Frame, Notebook

from ytsm.uis.gui_tk.views.settings_window.gui_settings_tab import GUISettingsTab
from ytsm.uis.gui_tk.views.settings_window.cli_settings_tab import CLISettingsTab
from ytsm.uis.gui_tk.views.settings_window.tui_settings_tab import TUISettingsTab

class SettingsView(Frame):
    """ Main Settings View frame """
    def __init__(self, master, restyle_gui_callback: Callable):
        super().__init__(master)
        self.notebook = Notebook(self)
        self.gui_settings = GUISettingsTab(self, restyle_gui_callback)
        self.tui_settings = TUISettingsTab(self)
        self.cli_settings = CLISettingsTab(self)
        # self.advanced_settings = Frame()

        self.notebook.add(self.gui_settings, text='GUI Settings', underline=0)
        self.notebook.add(self.tui_settings, text='TUI Settings', underline=0)
        self.notebook.add(self.cli_settings, text='CLI Settings', underline=0)
        # self.notebook.add(self.advanced_settings, text='Advanced Settings', state=DISABLED, underline=0)

        # Grid
        self.notebook.grid(row=0, column=0, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
