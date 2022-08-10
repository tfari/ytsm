""" CLI Settings tab, CLI Settings panel """
from typing import Callable
from tkinter import messagebox, StringVar, FLAT
from tkinter.ttk import Frame, Label, OptionMenu

from ytsm.settings import SETTINGS, VALID_CLI_COLORS
from ytsm.uis.gui_tk.views.settings_window.settings_lower_buttons_panel import SettingsLowerButtonsPanel


class CLISettingsTab(Frame):
    """ Tab for CLI Settings"""
    def __init__(self, master):
        super().__init__(master)
        self.cli_settings_panel = CLISettingsPanel(self, self.call_color_picker)
        self.frame_separator = Frame(self, height=3, style='TFrameSeparator.TFrame')
        self.bottom_bar = SettingsLowerButtonsPanel(self, self.call_save_settings, self.call_restore_settings)

        # Grid
        self.cli_settings_panel.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=2)
        self.frame_separator.grid(row=1, column=0, sticky='nsew')
        self.bottom_bar.grid(row=2, column=0, columnspan=3, sticky='nsew')

        self.grid_columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=99)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)

    @staticmethod
    def call_color_picker(color_value: str, attribute_name: str) -> None:
        """
        Set SETTINGS.cli_settings attribute_name's value to color_value
        """
        SETTINGS.cli_settings.__dict__[attribute_name] = color_value

    @staticmethod
    def call_save_settings() -> None:
        """ Save SETTINGS """
        save = messagebox.askyesno(f'Save ALL settings',
                                   f'Do you want to save ALL the changed settings (not only in this tab)?',
                                   icon=messagebox.WARNING)
        if save:
            SETTINGS.save_settings()

    def call_restore_settings(self) -> None:
        """
        Restore SETTINGS.cli_settings to default values.
        * Destroy and re-instance and regrid all the child Widgets to reflect the changes.
        """
        restore = messagebox.askyesno(f'Restore settings for CLISettings',
                                      f'Do you want to restore the factory settings for: CLISettings?',
                                      icon=messagebox.WARNING)
        if restore:
            SETTINGS.restore_settings(restore_type=type(SETTINGS.cli_settings))
            self.cli_settings_panel.destroy()
            self.cli_settings_panel = CLISettingsPanel(self, self.call_color_picker)
            self.cli_settings_panel.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=2)


class CLISettingsPanel(Frame):
    """ Panel for CLI Settings """
    def __init__(self, master, call_color_picker_callback: Callable):
        super().__init__(master)
        self.call_color_picker_callback = call_color_picker_callback
        self.cli_settings_label = Label(self, text='CLI Settings', style='TBigLabel.TLabel')

        for row_index, key in enumerate(SETTINGS.cli_settings.__dict__, start=2):  # Leave an empty row
            # Dynamically create Labels and OptionMenus for the cli settings, setting all OptionMenus commands to call
            # call_color_picker_callback with the selected value, and its associated attribute_name.
            label = Label(self, text=f'{" ".join([k.capitalize() for k in key.split("_")])}: ')
            val = StringVar()
            val.set(SETTINGS.cli_settings.__dict__[key])

            # Use settings.CLI_COLORS as options for the CLI colors
            option_menu = OptionMenu(self, val, SETTINGS.cli_settings.__dict__[key], *VALID_CLI_COLORS,
                                     command=lambda v=val, k=key: self.call_color_picker_callback(v, k))
            # Style the menus
            option_menu['menu'].config(
                activebackground=SETTINGS.gui_settings.colorscheme.background_active,
                background=SETTINGS.gui_settings.colorscheme.background,
                activeborderwidth=0,
                borderwidth=0,
                relief=FLAT,
                selectcolor=SETTINGS.gui_settings.colorscheme.accent,
                activeforeground=SETTINGS.gui_settings.colorscheme.foreground,
                foreground=SETTINGS.gui_settings.colorscheme.foreground)

            label.grid(row=row_index, column=0, sticky='nsew', padx=5)
            option_menu.grid(row=row_index, column=1, sticky='nsew', padx=5)

        # Grid
        self.cli_settings_label.grid(row=0, column=0, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
