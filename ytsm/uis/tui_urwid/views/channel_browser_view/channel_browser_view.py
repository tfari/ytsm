""" Channel Browser View """
from typing import Callable
from urwid import Button, Columns, LineBox, Edit, LEFT

from ytsm.uis.tui_urwid.widgets import CommandBar
from ytsm.uis.tui_urwid.views.base_view import BaseView
from ytsm.uis.tui_urwid.views.channel_browser_view.video_selector_pane import VideoSelectorPane
from ytsm.uis.tui_urwid.views.channel_browser_view.channel_selector_pane import ChannelSelectorPane

from ytsm.uis.ytsm_controller import YTSMController
from ytsm.settings import SETTINGS


class ChannelBrowserView(BaseView):
    """ Channel Browser View """
    def __init__(self, master, ytsm_controller: YTSMController, bottom_bar: CommandBar,
                 callback_open_video_detail_view: Callable):
        self.master = master
        self.ytsm_controller = ytsm_controller
        self.bottom_bar = bottom_bar
        self.callback_open_video_detail_view = callback_open_video_detail_view

        self.channel_select_pane = ChannelSelectorPane(self, ytsm_controller, bottom_bar,
                                                       self.callback_channel_selection,
                                                       self.callback_no_channels)
        self.video_select_pane = VideoSelectorPane(self, ytsm_controller, bottom_bar,
                                                   self.callback_open_video_detail_view,
                                                   self.callback_video_alterations)
        self.channel_linebox = LineBox(self.channel_select_pane, 'Channels', title_align=LEFT)
        self.video_linebox = LineBox(self.video_select_pane, 'Videos', title_align=LEFT)

        self.columns = Columns([self.channel_linebox, ('weight', 4, self.video_linebox)])

        # Bindings
        self.BINDINGS = {
            'TAB': self.toggle_focus_column_command,
            'LEFT': self.toggle_focus_column_command,
            'RIGHT': self.toggle_focus_column_command,
            SETTINGS.tui_settings.keybindings.update_all_channels_key.upper(): self.update_all_channels_command,
            SETTINGS.tui_settings.keybindings.add_channel_key.upper(): self.add_channel_command,
        }

        super().__init__(
            master=master,
            body=self.columns,
            title_bar_str='YTSM'
        )

    def keypress(self, size, key):
        """ Let tab keypress pass if Edit or Button are on focus, else try to parse via BINDINGS before sending to
        master """
        if (isinstance(self.get_focus_widgets()[-1], Edit) or isinstance(self.get_focus_widgets()[-1], Button)) and key\
                != 'tab':
            super().keypress(size, key)
        else:
            if key.upper() in self.BINDINGS.keys():
                self.BINDINGS[key.upper()]()
            else:
                self.master.keypress_callback(None, key)
                super().keypress(size, key)

    def keypress_callback(self, obj, key) -> None:
        """ Funnel keypress to master if not on self.BINDINGS """
        if key.upper() in self.BINDINGS.keys():
            self.BINDINGS[key.upper()]()

    def reload_view(self, reset_position: bool = False) -> None:
        """ Call a reload on channel_select_pane """
        self.channel_select_pane.reload_view(reset_position=reset_position)

    def callback_channel_selection(self, channel_dto: YTSMController.ChannelDTO) -> None:
        """ Callback for Channel selection action """
        self.video_linebox.set_title(f'{channel_dto.channel.name} videos')
        self.video_select_pane.reload_view(channel_dto.channel.idx, reset_position=True)

    def callback_video_alterations(self) -> None:
        """ Callback for Video alterations """
        self.channel_select_pane.reload_view()

    def callback_no_channels(self) -> None:
        """ Callback for when there are no Channels in the channel pane """
        self.video_select_pane.no_channels()

    def view_enter(self) -> None:
        """ View has been entered """
        self.video_select_pane.view_enter()

    # - COMMANDS

    def toggle_focus_column_command(self) -> None:
        """ Toggle the focused column when using left/right keys. """
        self.columns.set_focus(not self.columns.get_focus_column())

    def add_channel_command(self) -> None:
        """ Display add_channel prompt on bottom_bar """
        self.master.bottom_command_bar.display_prompt(self._add_channel_callback, 'Add a new channel')
        self.master.main_frame.focus_part = 'footer'  # TODO : Decouple this

    def _add_channel_callback(self, input_str: str) -> None:
        """ Callback for bottom_bar prompt on add_channel_command """
        try:
            new_channel = self.ytsm_controller.add_channel(input_str)
        except YTSMController.AddChannelError as e:
            self.master.bottom_command_bar.display_error(str(e))
        else:
            self.master.bottom_command_bar.display_message(f'Added channel: "{new_channel.name}"')
            self.reload_view()
        self.master.main_frame.focus_part = 'body'

    def update_all_channels_command(self) -> None:
        """ Update all channels """
        try:
            update_data = self.ytsm_controller.update_all_channels()
        except YTSMController.UpdateAllChannelsError as e:
            self.master.bottom_command_bar.display_error(str(e))
        else:
            amt = update_data['total']
            cns = ", ".join([f'"{ud[0]}"' for ud in update_data['details']])
            errs = f'Errors: {len(update_data["errs"])}. ' if update_data['errs'] else ''
            self.bottom_bar.display_message(f'Updated all channels: {errs}{amt} total new videos in channels: {cns}')
            self.reload_view()
