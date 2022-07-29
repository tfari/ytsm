""" GLOBAL SETTINGS ACCESS """
import dataclasses
import json
from collections.abc import Mapping
from typing import Union

NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO = 'NEW', 'UNWATCHED', 'OLD'

@dataclasses.dataclass
class GUIColorScheme(Mapping):
    """ Dataclass for holding GUI color scheme settings """
    # window_size: str = '854x700'

    accent: str = '#502B2B'
    background: str = '#292828'
    background_active: str = '#525151'
    background_darker: str = '#151414'

    entry_box_active: str = '#676565'
    entry_box_inactive: str = '#343232'

    foreground: str = '#D7D6D6'
    foreground_inactive: str = '#9A9898'

    foreground_old_video: str = '#9A9898'
    foreground_unwatched_video: str = '#236575'
    foreground_new_video: str = '#abff8c'

    def __getitem__(self, x):
        return self.__dict__[x]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

@dataclasses.dataclass
class GUIFontScheme(Mapping):
    """ Dataclass for holding GUI font settings """
    family_name: str = 'Monospace'
    normal_size: int = 10
    small_size: int = 8
    medium_size: int = 11
    big_size: int = 12

    def __getitem__(self, x):
        return self.__dict__[x]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

@dataclasses.dataclass
class GUISettings:
    """ Dataclass for holding all GUI Settings """
    colorscheme: Union[GUIColorScheme, dict] = GUIColorScheme()
    fontscheme: Union[GUIFontScheme, dict] = GUIFontScheme()
    scheduled_update_activated: bool = False
    scheduled_update_minutes: int = 15

    def __post_init__(self):
        self.colorscheme = GUIColorScheme(**self.colorscheme)
        self.fontscheme = GUIFontScheme(**self.fontscheme)

    def __dict__(self):
        return {'colorscheme': self.colorscheme.__dict__,
                'fontscheme': self.fontscheme.__dict__,
                'background_update_activated': self.scheduled_update_activated,
                'background_update_minutes': self.scheduled_update_minutes}


@dataclasses.dataclass
class CLISettings:
    """ Dataclass for holding all CLI settings """
    foreground_error: str = 'bright red'
    foreground_success: str = 'yellow'
    foreground_normal: str = 'white'

    foreground_old_video: str = 'white'
    foreground_unwatched_video: str = 'cyan'
    foreground_new_video: str = 'bright_green'


class Settings:
    """ All Settings """
    def __init__(self):
        self.path = None
        self.gui_settings = GUISettings()
        self.cli_settings = CLISettings()

    def set_path(self, path: str):
        """ Set a path for Settings """
        self.path = path

    def load_settings(self):
        """ Load settings """
        if self.path:
            with open(self.path, 'r', encoding='utf-8') as r_file:
                jsoned = json.load(r_file)

            self.gui_settings = GUISettings(**jsoned['gui_settings']) if jsoned.get('gui_settings') else GUISettings()
            self.cli_settings = CLISettings(**jsoned['cli_settings']) if jsoned.get('cli_settings') else CLISettings()
        else:
            raise(Settings.SettingsHasNoPath())

    def save_settings(self,):
        """ Save settings """
        if self.path:
            json_me = {'gui_settings': self.gui_settings.__dict__(),
                       'cli_settings': self.cli_settings.__dict__}

            with open(self.path, 'w', encoding='utf-8') as w_file:
                json.dump(json_me, w_file, indent=4)
        else:
            raise(Settings.SettingsHasNoPath())

    def restore_settings(self, *, restore_type=None):
        """ Restore settings to defaults, if restore_type is one of (GUISettings,), restore only that type of
        settings. """
        if not restore_type:
            self.gui_settings = GUISettings()
            self.cli_settings = CLISettings()
            self.save_settings()

        elif restore_type == GUISettings:
            self.gui_settings = GUISettings()
            self.save_settings()

    class SettingsHasNoPath(Exception):
        """ Settings has no associated path """


SETTINGS = Settings()
