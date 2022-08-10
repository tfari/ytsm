""" GUI Settings tab, GUI colorscheme, Fontscheme, Other options panels """
from typing import Callable
from tkinter import messagebox, Button, IntVar, BooleanVar, END, font, NORMAL, DISABLED
from tkinter.ttk import Frame, Label, Spinbox, Treeview, Scrollbar, Checkbutton
from tkinter.colorchooser import askcolor

from ytsm.settings import SETTINGS
from ytsm.uis.gui_tk.views.settings_window.settings_lower_buttons_panel import SettingsLowerButtonsPanel

class GUISettingsTab(Frame):
    """ Tab for the GUI Settings """
    def __init__(self, master, restyle_gui_callback: Callable):
        super().__init__(master)
        self.restyle_gui_callback = restyle_gui_callback
        self.color_scheme_panel = GUISettingsColorSchemePanel(self, self.call_color_picker)
        self.color_scheme_separator = Frame(self, width=3, style="TFrameSeparator.TFrame")
        self.fontscheme_panel = GUISettingsFontSchemePanel(self, self.call_number_picker, self.call_font_picker)
        self.other_options_separator = Frame(self, height=3, style='TFrameSeparator.TFrame')
        self.other_options_panel = GUISettingsOtherOptionsPanel(self, self.call_scheduled_update_changes,
                                                                self.call_window_on_top_changes)

        self.lower_separator = Frame(self, height=3, style="TFrameSeparator.TFrame")
        self.lower_button_panel = SettingsLowerButtonsPanel(self, self.call_save_settings, self.call_restore_settings)

        # Grid
        self.color_scheme_panel.grid(row=0, column=0, sticky='nsew', padx=2)
        self.color_scheme_separator.grid(row=0, column=1, rowspan=3, sticky='nsew')
        self.fontscheme_panel.grid(row=0, column=2, rowspan=3, sticky='nsew')
        self.other_options_separator.grid(row=1, column=0, sticky='nsew')
        self.other_options_panel.grid(row=2, column=0, sticky='nsew')
        self.lower_separator.grid(row=3, column=0, columnspan=3, sticky='nsew')
        self.lower_button_panel.grid(row=4, column=0, columnspan=3, sticky='nsew')

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=50)
        self.grid_rowconfigure(2, weight=50)
        self.grid_rowconfigure(4, weight=0)

    def call_color_picker(self, button_pressed: Button, attribute_name: str) -> None:
        """
        Present a color picker to the user, if he picks anything, alter button_called's background and
        SETTINGS.gui_settings.colorscheme attribute with name variable_name to this color.
        * Call the restyle_gui_callback method in order for the GUI to reflect the changes.

        :param button_pressed: The Button widget that was pressed
        :param attribute_name: The SETTINGS.gui_settings.colorscheme attribute's name associated to the button_pressed
        """
        picked_color = askcolor(SETTINGS.gui_settings.colorscheme.__dict__.get(attribute_name),
                                title=f'Pick color for "{attribute_name}"')

        if picked_color[1] is not None:  # color hex string
            SETTINGS.gui_settings.colorscheme.__dict__[attribute_name] = picked_color[1]
            # noinspection PyTypeChecker
            button_pressed.configure(background=picked_color[1])
        self.restyle_gui_callback()

    def call_number_picker(self, attribute_value: IntVar, attribute_name: str) -> None:
        """
        Set the value of SETTINGS.gui_settings.fontscheme attribute with name attribute_name to attribute_value.get().
        * Call the restyle_gui_callback method in order for the GUI to reflect the changes.

        :param attribute_value: The IntVar associated to the Spinbox whose value was altered
        :param attribute_name: The SETTINGS.gui_settings.fontscheme attribute's name associated to the altered spinbox
        """
        SETTINGS.gui_settings.fontscheme.__dict__[attribute_name] = attribute_value.get()
        self.restyle_gui_callback()

    def call_font_picker(self) -> None:
        """
        Set the selected item in self.fontscheme_panel.font_treeview as the font family name for
        SETTINGS.gui_settings.fontscheme.family_name.
        * Call the restyle_gui_callback method in order for the GUI to reflect the changes.
        """
        try:
            sel = self.fontscheme_panel.font_treeview.focus()
            SETTINGS.gui_settings.fontscheme.family_name = self.fontscheme_panel.font_treeview.item(sel)[
                'values'][0]
            self.restyle_gui_callback()
        except IndexError:  # Binding occurs before selection of current font family name
            pass

    @staticmethod
    def call_scheduled_update_changes(state: bool, amount_minutes: int) -> None:
        """
        Set the state for SETTINGS.gui_settings.scheduled_update_activated and/or the amount of minutes for
        SETTINGS.gui_settings.scheduled_update_minutes.
        """
        SETTINGS.gui_settings.scheduled_update_activated = state
        SETTINGS.gui_settings.scheduled_update_minutes = amount_minutes

    def call_window_on_top_changes(self, state: bool) -> None:
        """
        Set the state for SETTINGS.gui_settings.window_on_top.
        * Call the restyle_gui_callback method in order for the GUI to reflect the changes.
        """
        SETTINGS.gui_settings.window_on_top = state
        self.restyle_gui_callback()

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
        Restore SETTINGS.gui_settings to default values.
        * Call the restyle_gui_callback method in order for the GUI to reflect the changes.
        * Destroy and re-instance and regrid all the child Widgets to reflect the changes.
        """
        restore = messagebox.askyesno(f'Restore settings for GUISettings',
                                      f'Do you want to restore the factory settings for: GUISettings?',
                                      icon=messagebox.WARNING)
        if restore:
            SETTINGS.restore_settings(restore_type=type(SETTINGS.gui_settings))
            self.restyle_gui_callback()
            self.color_scheme_panel.destroy()
            self.fontscheme_panel.destroy()
            self.other_options_panel.destroy()

            self.color_scheme_panel = GUISettingsColorSchemePanel(self, self.call_color_picker)
            self.color_scheme_panel.grid(row=0, column=0, sticky='nsew', padx=2)
            self.fontscheme_panel = GUISettingsFontSchemePanel(self, self.call_number_picker, self.call_font_picker)
            self.fontscheme_panel.grid(row=0, column=2, rowspan=3, sticky='nsew')
            self.other_options_panel = GUISettingsOtherOptionsPanel(self, self.call_scheduled_update_changes,
                                                                    self.call_window_on_top_changes)
            self.other_options_panel.grid(row=2, column=0, sticky='nsew')

class GUISettingsColorSchemePanel(Frame):
    """ Color scheme panel """
    def __init__(self, master, call_color_picker_callback: Callable):
        super().__init__(master)
        self.call_color_picker_callback = call_color_picker_callback
        self.colorscheme_label = Label(self, text='Color Scheme', style='TBigLabel.TLabel')

        for row_index, key in enumerate(SETTINGS.gui_settings.colorscheme.__dict__, start=2):  # Leave an empty row
            # Dynamically create Labels and Buttons for the colorscheme, setting all Button commands to call
            # call_color_picker_callback with the Button widget itself, and its associated attribute_name.
            label = Label(self, text=f'{" ".join([k.capitalize() for k in key.split("_")])}: ')
            button = Button(self, text='')
            button.configure(background=SETTINGS.gui_settings.colorscheme.__dict__.get(key),
                             bd=0,
                             highlightbackground=SETTINGS.gui_settings.colorscheme.__dict__.get(key),
                             highlightcolor=SETTINGS.gui_settings.colorscheme.__dict__.get(key),
                             command=lambda b=button, k=key: self.call_color_picker_callback(b, k))
            label.grid(row=row_index, column=0, sticky='nsew', padx=5)
            button.grid(row=row_index, column=1, sticky='nsew', padx=5)

        # Grid
        self.colorscheme_label.grid(row=1, column=0, sticky='nsew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

class GUISettingsFontSchemePanel(Frame):
    """ Font scheme panel """
    def __init__(self, master, call_number_picker_callback: Callable, call_font_picker_callback: Callable):
        super().__init__(master)
        self.call_number_picker_callback = call_number_picker_callback
        self.call_font_picker_callback = call_font_picker_callback
        self.fontscheme_label = Label(self, text='Font Scheme', style='TBigLabel.TLabel')

        # Create widgets for altering font sizes setting all Spinbox commands to call call_number_picker_callback
        # with the associated IntVar and key_name.
        dicted_vals = [{'label_text': 'Small Size: ', 'label_style': 'TSmallLabel.TLabel', 'key_name': 'small_size'},
                       {'label_text': 'Normal Size: ', 'label_style': 'TLabel', 'key_name': 'normal_size'},
                       {'label_text': 'Medium Size: ', 'label_style': 'TMediumLabel.TLabel', 'key_name': 'medium_size'},
                       {'label_text': 'Big Size: ', 'label_style': 'TBigLabel.TLabel', 'key_name': 'big_size'}]

        for row_index, dv in enumerate(dicted_vals, start=2):  # Leave an empty row
            label = Label(self, text=dv['label_text'], style=dv['label_style'])
            val = IntVar()
            val.set(SETTINGS.gui_settings.fontscheme.__dict__[dv['key_name']])
            spinbox = Spinbox(self, from_=5, to=50, textvariable=val, state='readonly',
                              command=lambda v=val, k=dv['key_name']: self.call_number_picker_callback(v, k))
            label.grid(row=row_index, column=0, sticky='nsew', padx=7)
            spinbox.grid(row=row_index, column=1, sticky='nsew')

        self.font_separator = Frame(self, height=3, style="TFrameSeparator.TFrame")

        # Font names section Label, Treeview and Scrollbar,
        self.font_family_name_label = Label(self, text='Font Family Name: ', style='TBigLabel.TLabel')
        self.font_treeview = Treeview(self, columns=('Font Family Name',), show='', style='TSettingsTreeview.Treeview')
        self.font_treeview_scrollbar = Scrollbar(self, command=self.font_treeview.yview)
        self.font_treeview.config(yscrollcommand=self.font_treeview_scrollbar.set)

        font_family_names = sorted(list(set(font.families())) + ['Monospace'])
        selected_index = 0
        for index_ffn, ffn in enumerate(font_family_names):
            # Make tags for each font so that fonts are displayed in their own font
            self.font_treeview.tag_configure(ffn, font=font.Font(
                family=ffn, size=SETTINGS.gui_settings.fontscheme.normal_size),
                                             foreground=SETTINGS.gui_settings.colorscheme.foreground)
            self.font_treeview.insert('', END, str(index_ffn), values=(ffn,), tags=(ffn,))
            if ffn == SETTINGS.gui_settings.fontscheme.family_name:
                selected_index = index_ffn

        self.font_treeview.selection_set(str(selected_index))  # Select the current font
        self.font_treeview.see(str(selected_index))  # Scroll to it
        self.font_treeview.bind('<<TreeviewSelect>>', lambda x: self.call_font_picker_callback())  # Bind selection

        # Grid
        self.fontscheme_label.grid(row=0, column=0, sticky='nsew', padx=2)
        self.font_separator.grid(row=6, column=0, columnspan=3, sticky='nsew', pady=2)
        self.font_family_name_label.grid(row=7, column=0, sticky='nsew', padx=2, pady=2)
        self.font_treeview.grid(row=8, column=0, rowspan=20, columnspan=2, sticky='nsew', padx=7)
        self.font_treeview_scrollbar.grid(row=8, column=2, rowspan=20, sticky='nsew')

        self.grid_rowconfigure(8, weight=10)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

class GUISettingsOtherOptionsPanel(Frame):
    """ Other Options panel """
    def __init__(self, master, call_scheduled_update_callback: Callable, call_window_on_top_callback: Callable):
        super().__init__(master)
        self.call_scheduled_update_callback = call_scheduled_update_callback
        self.call_window_on_top_callback = call_window_on_top_callback
        self.other_options_label = Label(self, text='Other settings', style='TBigLabel.TLabel')

        # Scheduled updates
        self.scheduled_update_on_off_val = BooleanVar()
        self.scheduled_update_on_off_val.set(SETTINGS.gui_settings.scheduled_update_activated)
        self.scheduled_update_on_off = Checkbutton(self, text='Scheduled Updates',
                                                   variable=self.scheduled_update_on_off_val,
                                                   command=self.scheduled_update_changes)

        self.scheduled_updates_minutes_label = Label(self, text='Minutes between updates: ')
        self.scheduled_update_minutes_val = IntVar()
        self.scheduled_update_minutes_val.set(SETTINGS.gui_settings.scheduled_update_minutes)
        self.scheduled_update_minutes = Spinbox(self, from_=5, to=120, state='readonly',
                                                textvariable=self.scheduled_update_minutes_val,
                                                command=self.scheduled_update_changes)

        # Set scheduled_updates_minutes Label and Spinbox to DISABLED if scheduled_updates is OFF
        self.scheduled_updates_minutes_label.configure(state=NORMAL if self.scheduled_update_on_off_val.get() else
                                                       DISABLED)
        self.scheduled_update_minutes.configure(
            state='readonly' if self.scheduled_update_on_off_val.get() else DISABLED)

        # Window on top
        self.window_on_top_val = BooleanVar()
        self.window_on_top_val.set(SETTINGS.gui_settings.window_on_top)
        self.window_on_top = Checkbutton(self, text='Window On Top', variable=self.window_on_top_val,
                                         command=lambda: self.call_window_on_top_callback(self.window_on_top_val.get()))

        # Grid
        self.other_options_label.grid(row=0, column=0, sticky='nsew', padx=2)
        self.scheduled_update_on_off.grid(row=1, column=0, sticky='nsew', padx=7)
        self.scheduled_updates_minutes_label.grid(row=2, column=0, sticky='nsew', padx=15)
        self.scheduled_update_minutes.grid(row=2, column=1, sticky='nsew')
        self.window_on_top.grid(row=3, column=0, sticky='nsew', padx=7)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def scheduled_update_changes(self) -> None:
        """
        Changes on scheduled update, either on/off state, or amount of minutes
        """
        # Set scheduled_updates_minutes Label and Spinbox to DISABLED if scheduled_updates is OFF
        self.scheduled_updates_minutes_label.configure(state=NORMAL if self.scheduled_update_on_off_val.get() else
                                                       DISABLED)
        self.scheduled_update_minutes.configure(
            state='readonly' if self.scheduled_update_on_off_val.get() else DISABLED)

        # Call call_scheduled_update_callback with both on/off and minutes amount values
        self.call_scheduled_update_callback(self.scheduled_update_on_off_val.get(),
                                            self.scheduled_update_minutes_val.get())
