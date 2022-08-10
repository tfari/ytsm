""" Urwid based TUI """
import platform
import subprocess
from urwid import Frame, MainLoop, ExitMainLoop

from ytsm.ytsubmanager import YTSubManager
from ytsm.uis.ytsm_controller import YTSMController
from ytsm.uis.tui_urwid.widgets import CommandBar
from ytsm.uis.tui_urwid.views.help_view import HelpView
from ytsm.uis.tui_urwid.views.video_detail_view import VideoDetailView
from ytsm.uis.tui_urwid.views.all_videos_view import AllVideosView
from ytsm.uis.tui_urwid.views.channel_browser_view.channel_browser_view import ChannelBrowserView

from ytsm.settings import SETTINGS, NEW_VIDEO, OLD_VIDEO, UNWATCHED_VIDEO

class YTSMTui:
    """ Urwid based TUI """
    def __init__(self, ytsm: YTSubManager):
        self.ytsm_controller = YTSMController(ytsm)

        # Palette
        self.palette = [
            ('reversed', 'standout', '',),
            ('bold', 'bold', ''),
            ('title', 'bold, underline', ''),

            (NEW_VIDEO, SETTINGS.tui_settings.colorscheme.foreground_new_video, ''),
            (UNWATCHED_VIDEO, SETTINGS.tui_settings.colorscheme.foreground_unwatched_video, ''),
            (OLD_VIDEO, SETTINGS.tui_settings.colorscheme.foreground_old_video, ''),

            ('info_message', f'{SETTINGS.tui_settings.colorscheme.foreground_info}, bold', ''),
            ('error_message', f'{SETTINGS.tui_settings.colorscheme.foreground_error}, bold', ''),
            ('prompt_message', f'{SETTINGS.tui_settings.colorscheme.foreground_prompt}, bold', '')
        ]

        # Bindings
        self.BINDINGS = {
            SETTINGS.tui_settings.keybindings.quit_key.upper(): self.quit,
            SETTINGS.tui_settings.keybindings.quit_key_2.upper(): self.quit,
            SETTINGS.tui_settings.keybindings.help_toggle_key.upper(): self.toggle_help_view,
            SETTINGS.tui_settings.keybindings.open_settings_file_key.upper(): self.open_settings_file,
            SETTINGS.tui_settings.keybindings.all_videos_toggle_key.upper(): self.toggle_all_videos_view,
        }

        # Bottom Command bar
        self.bottom_command_bar = CommandBar(lambda x: None, '')
        self.bottom_command_bar.display_message('Welcome to YTSM - Press "h" for help.')

        # Views
        self.help_view = HelpView(self)
        self.all_videos_view = AllVideosView(self, self.ytsm_controller, self.bottom_command_bar,
                                             self.callback_open_video_detail_view)
        self.channel_browser_view = ChannelBrowserView(self, self.ytsm_controller, self.bottom_command_bar,
                                                       self.callback_open_video_detail_view)

        self.video_detail_view = None

        # Setup
        self.previous_view_history: list = []
        self.channel_browser_view.reload_view(reset_position=True)
        self.all_videos_view.reload_view(reset_position=True)

        self.main_frame = Frame(body=self.channel_browser_view, footer=self.bottom_command_bar)
        self.loop = MainLoop(self.main_frame, palette=self.palette, unhandled_input=self.unhandled_input)
        self.loop.screen.set_terminal_properties(colors=16)
        self.loop.run()

    def unhandled_input(self, event) -> None:
        """ Handle unhandled input """

    def keypress_callback(self, obj, key) -> None:
        """ Handle keypress callbacks from all Views """
        if key.upper() in self.BINDINGS.keys():
            self.BINDINGS[key.upper()]()

    def quit(self) -> None:
        """ Quit YTSM """
        if not self.previous_view_history:
            raise ExitMainLoop()
        else:
            if self.main_frame.body == self.all_videos_view:
                self.channel_browser_view.view_enter()  # Reload search terms when going out from Video view via quit
            self.main_frame.body = self.previous_view_history.pop()

    def toggle_help_view(self) -> None:
        """ Toggle HelpView """
        if self.main_frame.body == self.help_view:
            self.quit()
        else:
            self.previous_view_history.append(self.main_frame.body)
            self.main_frame.body = self.help_view

    def toggle_all_videos_view(self) -> None:
        """ Toggle AllVideos View """
        if self.main_frame.body == self.all_videos_view:
            self.channel_browser_view.view_enter()
            self.channel_browser_view.reload_view()
            self.main_frame.body = self.previous_view_history.pop()
        elif self.main_frame.body == self.channel_browser_view:
            self.all_videos_view.view_enter()
            self.all_videos_view.reload_view()
            self.previous_view_history.append(self.main_frame.body)
            self.main_frame.body = self.all_videos_view

    def callback_open_video_detail_view(self, video_dto: YTSMController.VideoDTO) -> None:
        """ Open VideoDetail View """
        self.previous_view_history.append(self.main_frame.body)
        self.video_detail_view = VideoDetailView(self, self.ytsm_controller, video_dto)
        self.main_frame.body = self.video_detail_view

    def open_settings_file(self) -> None:
        """ Open the settings file on the default application. """
        self.bottom_command_bar.display_message(f'Opened settings file. Restart the TUI to apply the changes.')
        if platform.system() == 'Darwin':
            subprocess.call(('open', SETTINGS.path))
        elif platform.system() == 'Linux':
            subprocess.call(('xdg-open', SETTINGS.path))
        else:
            self.bottom_command_bar.display_error(f'Could not recognize system name: {platform.system()}')
