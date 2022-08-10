""" Base View class """
from urwid import Frame, Text, AttrMap, CENTER

class BaseView(Frame):
    """ Base View Frame """
    def __init__(self, master, title_bar_str: str, body: Frame, use_top_bar: bool = True):
        self.master = master
        self.title_bar_str = title_bar_str
        self.title_bar_text = Text(title_bar_str, wrap='ellipsis', align=CENTER)
        self.title_bar = AttrMap(self.title_bar_text, 'reversed', focus_map='reversed') if use_top_bar else None

        super().__init__(header=self.title_bar, body=body)

    def keypress_callback(self, obj, key):
        """ Funnel keypress to self.master """
        self.master.keypress_callback(obj, key)

    def reload_view(self, *args):
        """ Reload the View """
        pass
