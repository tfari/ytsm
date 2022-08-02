"""
GLOBAL SETTINGS ACCESS
Implements the following constants:
SETTINGS -> A global Settings() class to use as a Singleton
NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO -> Constants for video tagging
CLI_COLORS -> A list of valid colorama colors for click usage
"""
import dataclasses
import json
from collections.abc import Mapping
from typing import Union

NEW_VIDEO, UNWATCHED_VIDEO, OLD_VIDEO = 'NEW', 'UNWATCHED', 'OLD'
CLI_COLORS = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red',
              'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white']

TUI_COLORS = ['black', 'dark red', 'dark green', 'brown', 'dark blue', 'dark magenta', 'dark cyan', 'light gray',
              'dark gray', 'light red', 'light green', 'yellow', 'light blue', 'light magenta', 'light cyan', 'white']


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
    window_on_top: bool = True
    default_window_size: tuple[int, int] = (854, 700)

    def __post_init__(self):
        self.colorscheme = GUIColorScheme(**self.colorscheme)
        self.fontscheme = GUIFontScheme(**self.fontscheme)

    def to_json(self) -> dict:
        """ Transform class to JSON serializable dict """
        # Transform dataclasses to dict, and add the normal key-value pairs
        return {'colorscheme': self.colorscheme.__dict__,
                'fontscheme': self.fontscheme.__dict__} | {k: self.__dict__[k] for k in self.__dict__.keys() if k not in
                                                           ('colorscheme', 'fontscheme')}


@dataclasses.dataclass
class CLISettings:
    """ Dataclass for holding all CLI settings """
    foreground_error: str = 'bright_red'
    foreground_success: str = 'yellow'
    foreground_normal: str = 'white'

    foreground_old_video: str = 'white'
    foreground_unwatched_video: str = 'cyan'
    foreground_new_video: str = 'bright_green'

    def __post_init__(self):
        """ Check all colors are in CLI_COLORS """
        for key in self.__dict__:
            if self.__dict__[key] not in CLI_COLORS:
                raise Settings.InvalidSettingsValue(f'In CLISettings: "{key}": "{self.__dict__[key]}", '
                                                    f'use one of these: {", ".join(CLI_COLORS)}')

# @dataclasses.dataclass
# class TUISettings:
#     """ Dataclass for holding all TUI Settings """
#     foreground_error: str = 'light red'
#     foreground_prompt: str = 'yellow'
#     foreground_info: str = 'light green'
#
#     foreground_old_video: str = 'white'
#     foreground_unwatched_video: str = 'light cyan'
#     foreground_new_video: str = 'light green'


@dataclasses.dataclass
class AdvancedSettings:
    """ Dataclass for advanced Settings """
    max_videos_per_channel: int = 100


class Settings:
    """ All Settings """

    def __init__(self):
        self.path = None
        self.gui_settings = GUISettings()
        self.cli_settings = CLISettings()
        self.advanced_settings = AdvancedSettings()

    def __dict__(self):
        return {'gui_settings': self.gui_settings.to_json(),
                'cli_settings': self.cli_settings.__dict__,
                'advanced_settings': self.advanced_settings.__dict__}

    def set_path(self, path: str) -> None:
        """ Set a path for Settings """
        self.path = path

    def load_settings(self) -> None:
        """
        Load settings
        :raises SettingsHasNoPath: if path has not been set
        :raises BrokenJSONFile: if the JSON file is broken
        :raises ExtraKeys: if the JSON file has extra keys
        :raises InvalidSettingsValue: if one of the values is invalid, ex: CLISettings not in CLI_COLORS
        """
        if not self.path:
            raise (Settings.SettingsHasNoPath())

        try:
            with open(self.path, 'r', encoding='utf-8') as r_file:
                jsoned = json.load(r_file)
        except json.decoder.JSONDecodeError as e:
            raise Settings.BrokenJSONFile(f'Broken JSON file: {str(e)}')
        else:
            try:
                # Load settings by key if they exist, else go for factory
                settings_map = {'gui_settings': GUISettings, 'cli_settings': CLISettings,
                                'advanced_settings': AdvancedSettings}
                for sett_key in settings_map:
                    if jsoned.get(sett_key):
                        setattr(self, sett_key, settings_map[sett_key](**jsoned[sett_key]))
                    else:
                        setattr(self, sett_key, settings_map[sett_key]())

            except TypeError as te:
                raise Settings.ExtraKeys(f'Extra keys: {str(te)}')

    def save_settings(self, ):
        """
        Save settings
        :raises SettingsHasNoPath: if path has not been set
        """
        if self.path:
            with open(self.path, 'w', encoding='utf-8') as w_file:
                json.dump(self.__dict__(), w_file, indent=4)
        else:
            raise (Settings.SettingsHasNoPath())

    def restore_settings(self, *, restore_type=None) -> None:
        """
        Restore settings to defaults, if restore_type is one of (GUISettings,), restore only that type of
        settings.
        :raises SettingsHasNoPath: if path has not been set.
        :raises TypeError: if restore_type is not empty, and it is not one of: (GUISettings, CLISettings)
        """
        if not restore_type:
            self.gui_settings = GUISettings()
            self.cli_settings = CLISettings()
            self.advanced_settings = AdvancedSettings()
        elif restore_type == GUISettings:
            self.gui_settings = GUISettings()
        elif restore_type == CLISettings:
            self.cli_settings = CLISettings()
        elif restore_type == AdvancedSettings:
            self.advanced_settings = AdvancedSettings()
        else:
            raise TypeError(restore_type)

        self.save_settings()

    class SettingsHasNoPath(Exception):
        """ Settings has no associated path """

    class BrokenJSONFile(Exception):
        """ Settings file has broken JSON """

    class ExtraKeys(Exception):
        """ Settings file has strange keys """

    class InvalidSettingsValue(Exception):
        """ Settings value is invalid """


SETTINGS = Settings()
