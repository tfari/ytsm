""" Reusable button panel for Save Settings / Restore Settings """
from typing import Callable
from tkinter.ttk import Frame, Button


class SettingsLowerButtonsPanel(Frame):
    """ Reusable button panel for Save Settings / Restore Settings """
    def __init__(self, master, save_settings_callback: Callable, restore_settings_callback: Callable):
        super().__init__(master)
        self.save_settings_button = Button(self, text='Save ALL settings', underline=0,
                                                       command=save_settings_callback)
        self.restore_settings_button = Button(self, text='Restore this tab\'s settings', underline=0,
                                                          command=restore_settings_callback)

        # Grid
        self.save_settings_button.grid(row=0, column=0, sticky='nsew')
        self.restore_settings_button.grid(row=0, column=1, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
