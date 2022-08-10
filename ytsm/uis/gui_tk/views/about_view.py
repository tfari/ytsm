""" About View """
import webbrowser
from tkinter.ttk import Frame, Label, Button

class AboutView(Frame):
    """ Displays app information """
    def __init__(self, master):
        super().__init__(master)
        self.about_label = Label(self, text='About YTSM', style='TBigLabel.TLabel')
        self.about_text_frame = Frame(self)
        self.visit_repo_button = Button(self, text='Visit repository', underline=0, command=self.visit_repository)

        # TODO: Use a multi-line entry
        desc_lines = ['YTSM is a YT Subscription manager.',
                      'Add, remove, and update any channels you want to follow.',
                      'Watch and keep a log of the videos you have watched.',
                      'To search for videos in a date range, the format is: "YYYY-MM-DD YYYY-MM-DD".',
                      'You can alter the feel of the GUI, CLI, and TUI via the Settings tab.',
                      'You can also schedule the GUI to search for updates every X amount of minutes while open.']

        for row_index, line in enumerate(desc_lines):
            label = Label(self.about_text_frame, text=f' + {line}')
            label.grid(row=row_index, column=0, padx=10, pady=2, sticky='nsew')

        # Grid
        self.about_label.grid(row=0, column=0, pady=10, sticky='ns')
        self.about_text_frame.grid(row=1, column=0, sticky='nsew')
        self.visit_repo_button.grid(row=2, column=0, sticky='nsew')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=99)
        self.rowconfigure(2, weight=1)

    @staticmethod
    def visit_repository() -> None:
        """ Open YTSM repository in the webbrowser """
        webbrowser.open('https://github.com/tfari/ytsm')