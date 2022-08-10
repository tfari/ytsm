""" Custom urwid widgets """
from typing import Callable

from urwid import AttrMap, Button, Edit, Frame, ListBox, Padding, \
    SimpleFocusListWalker, Text, CENTER, LEFT


class SelectableText(Text):
    """ Augmented Text widget that can be selected """
    def selectable(self) -> bool:
        """ Makes widget selectable """
        return True


class MenuButton(Button):
    """ Augmented Button widget that holds an object alongside its caption"""
    def __init__(self, caption: str, obj: object, align=None):
        self.caption = caption
        self.obj = obj
        super(MenuButton, self).__init__("")
        if not align:
            self._w = AttrMap(SelectableText(caption, wrap='ellipsis'), None, focus_map='reversed')
        else:
            self._w = AttrMap(SelectableText(caption, wrap='ellipsis', align=align), None, focus_map='reversed')


class VerticalScrollListBox(ListBox):
    """
    Augmented ListBox widget that scrolls with mouse scroll and notifies when its rendering,
    to use paired up with VerticalScrollFrame
    """
    def __init__(self, render_callback: Callable):
        super().__init__(SimpleFocusListWalker([]))
        self.render_callback = render_callback

    def load_data(self, data: list) -> None:
        """ Load data into SimpleFocusListWalker """
        self.body[:] = data

    def mouse_event(self, size, event, button, col, row, focus) -> None:
        """ Transform scrolls up and down into keypress events """
        if button == 4:
            self.keypress(size, 'up')
        elif button == 5:
            self.keypress(size, 'down')
        super().mouse_event(size, event, button, col, row, focus)

    def render(self, size, focus=False):
        """ Call self.render_callback (intended to be a VerticalScrollFrame's method)
        with self.ends_visible data """
        ends_visible = self.ends_visible(size)
        self.render_callback(ends_visible)
        return super().render(size, focus)

    def keypress(self, size, key):
        """ Send up/down key presses to parent, funnel the rest upwards """
        if key == 'up' or key == 'down':
            super().keypress(size, key)


class VerticalScrollFrame(Frame):
    """ Frame to hold VerticalScrollListBox and give it overflowing indicators """
    def __init__(self, top_bar_str: str = '', bottom_bar_str: str = '', padding_left: int = 0, padding_right: int = 0,
                 parent_render_callback: Callable = None, parent_keypress_callback: Callable = None):
        self.top_indicator_active = Text('▲', align=CENTER)
        self.top_indicator_inactive = Text(top_bar_str, align=CENTER)
        self.bottom_indicator_active = Text('▼', align=CENTER)
        self.bottom_indicator_inactive = Text(bottom_bar_str, align=CENTER)

        self.scroll_listbox = VerticalScrollListBox(self.render_callback)
        self.parent_render_callback = parent_render_callback
        self.parent_keypress_callback = parent_keypress_callback

        super().__init__(body=Padding(self.scroll_listbox, left=padding_left, right=padding_right),
                         header=self.top_indicator_inactive,
                         footer=self.bottom_indicator_active)

    def load_data(self, data, reset_position: bool = False) -> None:
        """ Load data into ListBox """
        self.scroll_listbox.load_data(data)
        if reset_position and (len(self.scroll_listbox.body) > 0):
            self.scroll_listbox.focus_position = 0

    def render_callback(self, end_visible) -> None:
        """
        Callback function when ListBox is rendering, make overflowing indicators visible or not visible depending
        on if end_visible contains 'bottom' or 'top'.
        """
        self.header = self.top_indicator_active
        self.footer = self.bottom_indicator_active

        if 'bottom' in end_visible:
            self.footer = self.bottom_indicator_inactive
        if 'top' in end_visible:
            self.header = self.top_indicator_inactive

        # Call parent render_callback with the index of the focused element
        if self.parent_render_callback:
            self.parent_render_callback(self.scroll_listbox.get_focus()[-1])

    def keypress(self, size, key) -> None:
        """ Handle selected objects, funnel the rest upwards """
        try:
            selected: MenuButton = self.scroll_listbox.get_focus_widgets()[0].base_widget.obj
        except IndexError:
            pass
        else:
            if self.parent_keypress_callback:
                self.parent_keypress_callback(selected, key)
        super().keypress(size, key)


class CommandBar(Edit):
    """ Augmented Edit widget that can display messages, errors, and prompt users for both free text and options """
    def __init__(self, callback, caption: str, align=LEFT):
        self.callback = callback
        self.valid_options: list = []
        super().__init__(caption=caption, align=align)

    def keypress(self, size, key) -> None:
        """ Take care of input. If user is attempting to submit text, call self.callback(input_text) """
        if key == 'enter':  # User is attempting to submit text
            input_text = self.edit_text.strip()
            if self.valid_options:  # If this is not empty we are capturing options
                options = [vo.upper() for vo in self.valid_options]  # Normalize case
                if input_text.upper() not in options:
                    return None
            self.callback(input_text.strip())
        else:
            super().keypress(size, key)

    def clear(self) -> None:
        """ Clear the bar's text """
        self.edit_text = u''
        self.set_caption('')
        self.valid_options = []

    def display_message(self, message: str, *, palette: str = 'info_message') -> None:
        """ Display a message """
        self.clear()
        self.set_caption((palette, message))

    def display_error(self, message: str, *, palette: str = 'error_message') -> None:
        """ Display an error """
        self.clear()
        self.set_caption((palette, message))

    def display_prompt(self, callback, prompt: str, valid_options: list[str] = None, *,
                       palette: str = 'prompt_message') -> None:
        """ Display a prompt. If valid_options is passed, the user is forced to input one of its members. (No-case) """
        self.clear()
        self.callback = callback
        if valid_options:
            prompt += f' [{"/".join(valid_options)}]'
            self.valid_options = valid_options
        self.set_caption((palette, f'{prompt}: '))
