""" TUI Settings tab, TUI Colorscheme panel, TUI Keybinding panel """
from typing import Callable
from tkinter import FLAT, StringVar, messagebox
from tkinter.ttk import Entry, Frame, Label, OptionMenu

from ytsm.settings import SETTINGS, VALID_TUI_COLORS
from ytsm.uis.gui_tk.views.settings_window.settings_lower_buttons_panel import SettingsLowerButtonsPanel


class TUISettingsTab(Frame):
    """ Tab for TUI Settings """
    def __init__(self, master):
        super().__init__(master)
        self.color_scheme_panel = TUISettingsColorSchemePanel(self, self.call_color_picker)
        self.frame_separator_1 = Frame(self, height=3, style='TFrameSeparator.TFrame')
        self.key_binding_panel = TUISettingsKeyBindingPanel(self, self.call_key_picker)
        self.frame_separator_2 = Frame(self, height=3, style='TFrameSeparator.TFrame')
        self.lower_button_panel = SettingsLowerButtonsPanel(self, self.call_save_settings, self.call_restore_settings)

        # Grid
        self.color_scheme_panel.grid(row=0, column=0, sticky='nsew', padx=2)
        self.frame_separator_1.grid(row=1, column=0, sticky='nsew')
        self.key_binding_panel.grid(row=2, column=0, sticky='nsew', padx=2)
        self.frame_separator_2.grid(row=3, column=0, sticky='nsew')
        self.lower_button_panel.grid(row=4, column=0, sticky='nsew')

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

    @staticmethod
    def call_color_picker(color_value: str, attribute_name: str) -> None:
        """ Set SETTINGS.tui_settings.colorscheme attribute_name's value to color_value """
        SETTINGS.tui_settings.colorscheme.__dict__[attribute_name] = color_value

    @staticmethod
    def call_key_picker(attribute_name: str, attribute_value: str) -> None:
        """Set SETTINGS.tui_settings.keybindings attribute_name's value to color_value """
        print(attribute_name, attribute_value)
        SETTINGS.tui_settings.keybindings.__dict__[attribute_name] = attribute_value

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
        restore = messagebox.askyesno(f'Restore settings for TUISettings',
                                      f'Do you want to restore the factory settings for: TUISettings?',
                                      icon=messagebox.WARNING)
        if restore:
            SETTINGS.restore_settings(restore_type=type(SETTINGS.tui_settings))
            self.color_scheme_panel.destroy()
            self.key_binding_panel.destroy()
            self.color_scheme_panel = TUISettingsColorSchemePanel(self, self.call_color_picker)
            self.key_binding_panel = TUISettingsKeyBindingPanel(self, self.call_key_picker)
            self.color_scheme_panel.grid(row=0, column=0, sticky='nsew', padx=2)
            self.key_binding_panel.grid(row=2, column=0, sticky='nsew', padx=2)

class TUISettingsColorSchemePanel(Frame):
    """ Panel for TUI Colorscheme Settings"""
    def __init__(self, master, call_color_picker_callback: Callable):
        super().__init__(master)
        self.call_color_picker_callback = call_color_picker_callback
        self.tui_colorscheme_label = Label(self, text='TUI Colorscheme Settings', style='TBigLabel.TLabel')

        for row_index, key in enumerate(SETTINGS.tui_settings.colorscheme.__dict__, start=2):  # Leave an empty row
            # Dynamically create Labels and OptionMenus for the cli settings, setting all OptionMenus commands to call
            # call_color_picker_callback with the selected value, and its associated attribute_name.
            label = Label(self, text=f'{" ".join([k.capitalize() for k in key.split("_")])}: ')
            val = StringVar()
            val.set(SETTINGS.tui_settings.colorscheme.__dict__[key])

            # Use settings.CLI_COLORS as options for the CLI colors
            option_menu = OptionMenu(self, val, SETTINGS.tui_settings.colorscheme.__dict__[key], *VALID_TUI_COLORS,
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
        self.tui_colorscheme_label.grid(row=0, column=0, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)


class TUISettingsKeyBindingPanel(Frame):
    """ Panel for TUI Key Binding Settings"""
    def __init__(self, master, call_key_picker_callback: Callable):
        super().__init__(master)
        self.call_key_picker_callback = call_key_picker_callback
        self.tui_keybinding_label = Label(self, text='TUI Key Binding Settings', style='TBigLabel.TLabel')

        for row_index, key in enumerate(SETTINGS.tui_settings.keybindings.__dict__, start=2):  # Leave an empty row
            # Dynamically create Labels and OptionMenus for the cli settings, setting all OptionMenus commands to call
            # call_color_picker_callback with the selected value, and its associated attribute_name.
            label = Label(self, text=f'{" ".join([k.capitalize() for k in key.split("_")])}: ')
            val = StringVar(value=SETTINGS.tui_settings.keybindings.__dict__[key])
            entry = Entry(self, textvariable=val)
            entry.bind("<KeyRelease>", lambda e, k=key, v=val: self.call_key_picker_callback(k, v.get()))
            label.grid(row=row_index, column=0, sticky='nsew', padx=5)
            entry.grid(row=row_index, column=1, sticky='nsew', padx=5)

        # Grid
        self.tui_keybinding_label.grid(row=0, column=0, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
