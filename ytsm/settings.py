""" Settings """
import json

import dataclasses
from ytsm.logger import Logger

@dataclasses.dataclass
class Settings:
    """ Settings dataclass """
    settings_v: str = '0.0.1'

    error_msg_color: str = 'red'
    success_msg_color: str = 'green'
    info_msg_color: str = 'yellow'

    new_videos_color: str = 'light green'
    unwatched_videos_color: str = 'dark cyan'
    watched_videos_color: str = 'white'

    repo_type: str = 'sql'

def load_settings(settings_file_path: str, logger: Logger) -> Settings:
    """ Load Settings from file, or generate a new file if needed """
    try:
        with open(settings_file_path, 'r', encoding='utf-8') as r_file:
            return Settings(**json.load(r_file))
    except FileNotFoundError:
        settings = Settings()
        save_settings(settings, settings_file_path)
        logger.err(f'Settings file not found on {settings_file_path}. Created a new one...', fatal=False)
        return settings
    except json.decoder.JSONDecodeError as exception:
        raise BrokenJSONSettings(exception)

def save_settings(settings: Settings, settings_file_path: str):
    """ Save settings as JSON file """
    json.dump(settings.__dict__, open(settings_file_path, 'w', encoding='utf-8'), indent=4)


class BrokenJSONSettings(Exception):
    """ Settings file has broken JSON """
