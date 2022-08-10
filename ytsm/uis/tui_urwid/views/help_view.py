""" View for displaying Help information """
from urwid import AttrMap, CENTER

from ytsm.uis.tui_urwid.views.base_view import BaseView
from ytsm.uis.tui_urwid.widgets import MenuButton, VerticalScrollFrame

from ytsm.settings import SETTINGS
class HelpView(BaseView):
    """ View for displaying Help information """
    def __init__(self, master):
        qk = SETTINGS.tui_settings.keybindings.quit_key.upper()
        qk2 = SETTINGS.tui_settings.keybindings.quit_key_2.upper()
        hk = SETTINGS.tui_settings.keybindings.help_toggle_key.upper()
        sk = SETTINGS.tui_settings.keybindings.open_settings_file_key.upper()
        avk = SETTINGS.tui_settings.keybindings.all_videos_toggle_key.upper()
        uak = SETTINGS.tui_settings.keybindings.update_all_channels_key.upper()
        ack = SETTINGS.tui_settings.keybindings.add_channel_key.upper()
        uck = SETTINGS.tui_settings.keybindings.update_channel_key.upper()
        rck = SETTINGS.tui_settings.keybindings.remove_channel_key.upper()
        mtk = SETTINGS.tui_settings.keybindings.toggle_mute_notifications_key.upper()
        mwk = SETTINGS.tui_settings.keybindings.mark_watched_key.upper()
        obk = SETTINGS.tui_settings.keybindings.open_on_browser_key.upper()
        vdk = SETTINGS.tui_settings.keybindings.video_details_key.upper()

        self.help_scroll = VerticalScrollFrame(parent_keypress_callback=self.keypress_callback)
        self.help_scroll.load_data([
            AttrMap(MenuButton('YTSM - Youtube Subscription Manager', None, align=CENTER), 'bold'),
            AttrMap(MenuButton('', None), 'normal'),
            AttrMap(MenuButton(f'{qk} / {qk2} : Quit (Go back if not on Browser View)', None, align=CENTER), 'normal'),
            AttrMap(MenuButton(f'{hk} : Toggle help window', None, align=CENTER), 'normal'),
            AttrMap(MenuButton(f'{sk} : Open settings file', None, align=CENTER), 'normal'),
            AttrMap(MenuButton(f'{avk} : Toggle Video list mode', None, align=CENTER), 'normal'),
            AttrMap(MenuButton('', None), 'normal'),
            AttrMap(MenuButton(f'{uak} : Update all Channels', None, align=CENTER), 'normal'),
            AttrMap(MenuButton(f'{ack} : Add a new Channel', None, align=CENTER), 'normal'),
            AttrMap(MenuButton('', None), 'normal'),
            AttrMap(MenuButton(f'{uck} : Update a Channel', None, align=CENTER), 'normal'),
            AttrMap(MenuButton(f'{rck} : Remove a Channel', None, align=CENTER), 'normal'),
            AttrMap(MenuButton(f'{mtk} : Toggle mute notifications on a Channel', None, align=CENTER), 'normal'),
            AttrMap(MenuButton('', None), 'normal'),
            AttrMap(MenuButton(f'{mwk} : Mark Video as watched, or all Videos in a Channel', None, align=CENTER),
                    'normal'),
            AttrMap(MenuButton(f'{obk} : Open a Video on web-browser, or visit Channel', None, align=CENTER),
                    'normal'),
            AttrMap(MenuButton(f'{vdk} : View Video\'s details', None, align=CENTER), 'normal'),
        ], reset_position=True)

        super().__init__(master=master,
                         title_bar_str='YTSM - Help',
                         body=self.help_scroll)
