""" Entry-point """
import os
import sys
import webbrowser
import subprocess

from logging import INFO
from typing import Optional, Any

import click

from ytsm import ytsubmanager, repository, settings, logger, model
# from ytsm.uis.gui_tk import ytsm_gui
# from ytsm.uis.tui_urwid import ytsm_tui

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = f'{SCRIPT_PATH}/data'

LOG_FILEPATH = f'{DATA_PATH}/log.log'
SETTINGS_FILEPATH = f'{DATA_PATH}/settings.json'
SQL_REPO_FILEPATH = f'{DATA_PATH}/ytsm'

LOGGER: logger.Logger
YTSM: ytsubmanager.YTSubManager


def _error_echo(err_msg: str, fatal: bool = True):
    """ Echo for errors, if fatal, exit application. Red foreground color."""
    click.secho(f'[!] {err_msg}', fg='red')
    if fatal:
        sys.exit(1)

def _success_echo(msg: str):
    """ Echo for successful operations. Yellow foreground color. """
    click.secho(f'[*] {msg}', fg='yellow')

def _echo(msg: str, fg_color: str = 'white'):
    """ Normal echo, white foreground color by default. """
    click.secho(msg, fg=fg_color)

def _echo_channels(channel_list: list[model.Channel]):
    """ Echo a list of channels """
    for c in channel_list:
        total, new, unwatched = YTSM.get_amt_videos(channel_id=c.idx)
        color = 'green' if new else 'blue' if unwatched else 'white'
        _echo(f'\t{c.name} - New: {new} / Unwatched: {unwatched} / Total: {total}', color)

def _echo_videos(video_list: list[model.Video], show_channel_name: bool = False):
    """ Echo a list of videos """
    for video in video_list:
        color = 'green' if video.new else 'blue' if not video.watched else 'white'
        _echo(f'\t{video.sensible_pubdate()} - '
              f'{YTSM.get_channel(video.channel_id).name + " - " if show_channel_name else ""} {video.name}', color)

    for video in video_list:  # TODO: Put on parallel thread? Why does this take so long? Because of .commit()
        YTSM.mark_video_as_old(video.idx)

def _find_and_confirm(s_term: str, possibilities: list, obj_name: str) -> Optional[Any]:
    """ Find and confirm either a Channel or Video from a list of possibilities. If there is only one possibility,
    return that possibility. """
    confirmed_element = None

    if not possibilities:
        _error_echo(f'No {obj_name} found for search term: {s_term}', fatal=False)
    elif len(possibilities) == 1:
        return possibilities[0]
    else:
        separator = '\n\t'
        n = click.prompt(f'Found the following possible {len(possibilities)} {obj_name}. Which is it? {separator}'
                         f'{separator.join([f"{i} - {p.name}" for i, p in enumerate(possibilities)])}\n',
                         prompt_suffix=' > ',
                         type=click.Choice(['EXIT'] + [str(i) for i in range(0, len(possibilities))],
                                           case_sensitive=False))
        if n != 'EXIT':
            confirmed_element = possibilities[int(n)]

    return confirmed_element

@click.group()
def ytsm():
    """ YTSM is a YT Subscription manager. Add, remove, and update any channels you want to follow, watch and keep a
    log of the videos you have watched.

    https://github.com/tfari/ytsm
    """
    global LOGGER, YTSM
    # 1 - If no data information exists, create it
    if not os.path.exists(DATA_PATH):
        print(f'[*] Creating data...')
        _factory_restore()
    # 2 - If no sql_repo_filepath exists, create it
    if not os.path.exists(SQL_REPO_FILEPATH):
        _factory_restore(all=False, db=True)

    # 3 - Load the logger
    LOGGER = logger.Logger(logger.Logger.logger_setup('ytsm.log', LOG_FILEPATH, INFO))

    # 4 - Load settings
    # SETTINGS = settings.load_settings(SETTINGS_FILEPATH, LOGGER)

    # 5 - Load repo
    repo = repository.SQLiteRepository(db_path=SQL_REPO_FILEPATH)

    # 6 - Load YTSM instance
    YTSM = ytsubmanager.YTSubManager(repository=repo)


@click.command('factory-restore')
@click.option('--all', is_flag=True, help='Restore everything to factory')
@click.option('--setts', is_flag=True, help='Restore the user settings')
@click.option('--db', is_flag=True, help='Restore the database')
def factory_restore(all: bool = True, setts: bool = False, db: bool = False) -> None:
    """
    Restore the data for the application to factory, either everything, or only the settings and/or db.
    """
    _factory_restore(all, setts, db)

def _factory_restore(all: bool = True, setts: bool = False, db: bool = False) -> None:
    """
    Indirect function. We use this because we want to use this logic when the app is used for the first time. Because
    of how click works, the creation fails is the user attempts to use any commands before the data is there if the
    logic inside this function were to be directly on a click decorated one, by dividing into an exposed decorated
    func and a protected one for its logic, we can safely call the protected one on ytsm() upon detection of no
    data/ folder.
    """
    if not all and not setts and not db:
        _error_echo(f'Command must be called with at least one of the options: "--all", "--setts", "--db"')

    if all:  # Restore all the data to factory settings
        setts, db = True, True
        if not os.path.exists(DATA_PATH):  # If there is no folder, create it.
            _success_echo(f'Creating new directory at {DATA_PATH}...')
            try:
                os.makedirs(DATA_PATH)
            except Exception as e:
                _error_echo(f'Fatal error, failed at creation of data folder at "{SCRIPT_PATH}" with error: {e}')

    if setts:
        if os.path.exists(SETTINGS_FILEPATH):
            _success_echo(f'Removing old settings file...')
            os.remove(SETTINGS_FILEPATH)
        _success_echo(f'Creating new settings.json file at {SETTINGS_FILEPATH}...')
        settings.save_settings(settings.Settings(), SETTINGS_FILEPATH)

    if db:
        if os.path.exists(SQL_REPO_FILEPATH):
            _success_echo(f'Removing old db file...')
            os.remove(SQL_REPO_FILEPATH)
        _success_echo(f'Creating new db file at {SQL_REPO_FILEPATH}...')
        repository.SQLiteRepository.create_db(SQL_REPO_FILEPATH)

@click.command('notify-update')
def notify_update():
    """
    Update all channels and notify the changed ones. For usage with crontab or other scheduling of commands.
    This implementation uses the "notify-send" tool to access the system's notification tray.
    More info on: https://vaskovsky.net/notify-send/
    """
    updates = []
    channels = YTSM.get_all_channels()
    for c in channels:
        new = YTSM.update_channel(c.idx)
        if new != 0:
            updates.append(c.name)

    if updates:
        message = f'New videos on {", ".join(updates)}'
        subprocess.run(['notify-send', 'YTSM', message])


@click.command('channels')
@click.option('--new', '-n', is_flag=True, help='Show only channels with new videos')
@click.option('--unwatched', '-u', is_flag=True, help='Show only channels with unwatched videos')
def list_channels(new: bool = False, unwatched: bool = False):
    """ List all channels. If -n is passed show only channels with new videos, if -u is passed show only channels
    with unwatched videos. """
    _success_echo('Listing channels with new videos:'
                  if new else 'Listing channels with unwatched videos:' if unwatched else 'Listing all channels:')
    channels = sorted(YTSM.get_all_channels(), key=lambda x: x.name.lower())
    filtered_channels = [c for c in channels]
    for c in channels:
        videos = YTSM.get_all_videos(channel_id=c.idx)
        new_videos = sum([1 for v in videos if v.new])
        unwatched_videos = sum([1 for v in videos if not v.watched])
        if (new and new_videos == 0) or (unwatched and unwatched_videos == 0):
            filtered_channels.remove(c)

    _echo_channels(filtered_channels)


@click.command('add')
@click.argument('URL', type=str)
def add_channel(url: str):
    """ Add a channel via a yt url. Accepted URL types: "/channel", "/user", "/watch" """
    try:
        c_id = YTSM.add_channel(url)
    except YTSM.BaseYTSMError as e:
        _error_echo(f'{type(e).__name__}: {str(e)}')
    else:
        _success_echo(f'Added channel: "{YTSM.get_channel(c_id).name}"')


@click.command('remove')
@click.argument('NAME', type=str)
def remove_channel(name: str):
    """ Remove a channel by its name """
    deleting_channel: Optional[model.Channel] = _find_and_confirm(name, YTSM.find_channels(name), 'channels')
    if deleting_channel:
        if click.confirm(f'Are you sure you want to remove channel: "{deleting_channel.name}"?', prompt_suffix=' > '):
            YTSM.remove_channel(deleting_channel.idx)
            _success_echo(f'Deleted channel: "{deleting_channel.name}"')


@click.command('update')
@click.argument('NAME', default=None, type=str, required=False)
@click.option('-a', is_flag=True, help='Update all channels')
def update_channel(name: str, a: bool) -> None:
    """ Update a channel, or all channels if -a is passed. """
    if not a and not name:
        _error_echo(f'Either pass a name to update, or the -a option to update all channels.')  # Fatal err

    if a:
        try:
            _success_echo(f'Updating {len(YTSM.get_all_channels())} channels, this might take a while...')
            n_videos = YTSM.update_all_channels()
        except YTSM.BaseYTSMError as e:
            _error_echo(f'{type(e).__name__}: {str(e)}')  # Fatal err
        else:
            _success_echo(f'Found: {n_videos} new videos.')
            return None  # Return when finished, no name and -a allowed

    if name:
        updating_channel: Optional[model.Channel] = _find_and_confirm(name, YTSM.find_channels(name), 'channels')
        if updating_channel:
            try:
                n_videos = YTSM.update_channel(channel_id=updating_channel.idx)
            except YTSM.BaseYTSMError as e:
                _error_echo(f'{type(e).__name__}: {str(e)}')  # Fatal err
            else:
                _success_echo(f'Updated channel: {updating_channel.name} and found {n_videos} new videos.')

@click.command('visit')
@click.argument('NAME', type=str)
def visit_channel(name: str):
    """ Visit a Channel's YTSM page """
    visiting_channel: Optional[model.Channel] = _find_and_confirm(name, YTSM.find_channels(name), 'channels')
    if visiting_channel:
        webbrowser.open(f'https://www.youtube.com/channel/{visiting_channel.idx}')

@click.command('find')
@click.argument('TERM', required=False)
@click.option('-v', '--videos', is_flag=True, help='Find in videos instead')
@click.option('-d', '--description', is_flag=True, help='Find videos by description')
@click.option('--date', nargs=2, required=False, help='Find videos by date range')
@click.option('--channel-name', required=False, help='Find videos only within a specific channel')
def find(term: str, videos: bool = False, description: bool = False, date: tuple[str, str] = None,
         channel_name: str = None):
    """ Find channels by name. If -v is passed, find videos by name, if -d is passed, it finds videos by
    description, if --date is passed, find videos by date range. If --channel-name is passed, only search within
    a specific channel.
    --date takes two dates in the form YYYY-MM-DD to search in between.
    """
    if not videos:
        if not term:
            _error_echo(f'Need a TERM when searching channels by name')  # Fatal
        _success_echo(f'Found channels by name like: "{term}"')
        channel_list = YTSM.find_channels(term)
        _echo_channels(channel_list)

    else:
        if not term and not date:
            _error_echo(f'Need a TERM when searching videos by any other thing than a DATE RANGE')  # Fatal

        potential_channel = __find_potential_channel(channel_name)
        potential_channel_idx = potential_channel.idx if potential_channel else None

        channel_specific_msg = f'{(", in channel: " + potential_channel.name) if potential_channel else ""}'
        if description:
            _success_echo(f'Found videos by desc like: "{term}"{channel_specific_msg}')
            video_list = YTSM.find_video_by_desc(term, channel_id=potential_channel_idx)
        elif date:
            _success_echo(f'Found videos by date_range between: "{date[0]}" and "{date[1]}"{channel_specific_msg}')
            video_list = YTSM.get_all_videos_by_date_range(date[0], date[1], channel_id=potential_channel_idx)
        else:  # (NAME)
            _success_echo(f'Found videos by name like: "{term}"{channel_specific_msg}')
            video_list = YTSM.find_video_by_name(term, channel_id=potential_channel_idx)

        _echo_videos(sorted(video_list, key=lambda x: x.pubdate, reverse=True), show_channel_name=True)

def __find_potential_channel(channel_name: Optional[str]) -> Optional[model.Channel]:
    """ Helper: Attempts to find a potential channel for the find() command. """
    if channel_name:
        potential_channel = _find_and_confirm(channel_name, YTSM.find_channels(channel_name), 'channel')
        if not potential_channel:
            _error_echo(f'No channel selected')  # Fatal
        else:
            return potential_channel
    return None


@click.command('videos')
@click.argument('CHANNEL_NAME', type=str, default=None, required=False)
@click.option('--new', '-n', is_flag=True, help='Only show new videos.')
@click.option('--unwatched', '-u', is_flag=True, help='Only show unwatched videos.')
@click.option('--limit', '-l', type=int, help='The amount of videos to show', required=False, default=15)
@click.option('--no-limit', '-nl', is_flag=True, help='No limit on the amount of videos shown.')
def list_videos(channel_name: str, new: bool = False, unwatched: bool = False, limit: int = 15, no_limit: bool = False):
    """ List the last 15 videos of CHANNEL_NAME (if not passed, it lists the last 15 videos of all channels).
    Using --new/-n or --unwatched/-u you can filter the videos to only new or unwatched respectively.
    You can set the amount of videos to show using --limit/-l, or use --no-limit/-nl to show all videos. """
    channel_idx = None
    viewing_channel = None
    if channel_name:
        viewing_channel = _find_and_confirm(channel_name, YTSM.find_channels(channel_name), 'channels')
        if not viewing_channel:
            _error_echo(f'No channel selected')
        else:
            channel_idx = viewing_channel.idx

    video_list = YTSM.get_all_new_videos(channel_id=channel_idx) if new else YTSM.get_all_unwatched_videos(
        channel_id=channel_idx) if unwatched else YTSM.get_all_videos(channel_id=channel_idx)

    videos = sorted(video_list, key=lambda x: x.pubdate, reverse=True)
    videos = videos if no_limit else videos[:limit]
    filter_msg_part = f'new' if new else 'unwatched' if unwatched else ''
    limit_msg_part = f'Viewing last {len(videos)}/{limit} {filter_msg_part} videos' \
        if not no_limit else f'Viewing all {len(videos)} videos'
    channel_msg_part = f' of channel "{viewing_channel.name}"' if viewing_channel else ''
    _success_echo(f'{limit_msg_part}{channel_msg_part}:')
    _echo_videos(videos, show_channel_name=True if not channel_idx else False)

@click.command('detail')
@click.argument('NAME', type=str)
def video_detail(name: str):
    """ Show the details of a video (name, channel, publication date, description) """
    detail_video = _find_and_confirm(name, YTSM.find_video_by_name(name), 'videos')
    if detail_video:
        _echo(detail_video.name, 'green' if detail_video.new else 'blue' if not detail_video.watched else 'white')
        _echo(YTSM.get_channel(detail_video.channel_id).name, 'yellow')
        _echo(detail_video.sensible_pubdate())
        _echo(detail_video.description)


@click.command('watch')
@click.argument('NAME', type=str)
def watch_video(name: str):
    """ Open a video in your web browser, and mark it as watched."""
    watched_video = _find_and_confirm(name, YTSM.find_video_by_name(name), 'videos')
    if watched_video:
        webbrowser.open(watched_video.url)
        YTSM.mark_video_as_old(watched_video.idx)
        YTSM.mark_video_as_watched(watched_video.idx)


@click.command('watched')
@click.argument('NAME')
@click.option('-c', is_flag=True)
def mark_watched(name: str, c: bool = False):
    """ Mark a video as watched, or all videos in a channel if -c is passed. """
    if c:
        mark_channel_watched_and_old = _find_and_confirm(name, YTSM.find_channels(name), 'channels')
        if mark_channel_watched_and_old:
            YTSM.mark_all_videos_old(mark_channel_watched_and_old.idx)
            YTSM.mark_all_videos_watched(mark_channel_watched_and_old.idx)
            _success_echo(f'Marked all videos in "{mark_channel_watched_and_old.name}" as watched.')
    else:
        mark_video_watched_and_old = _find_and_confirm(name, YTSM.find_video_by_name(name), 'videos')
        if mark_video_watched_and_old:
            YTSM.mark_video_as_old(mark_video_watched_and_old.idx)
            YTSM.mark_video_as_watched(mark_video_watched_and_old.idx)
            _success_echo(f'Marked video: "{mark_video_watched_and_old.name}" in channel: '
                          f'"{YTSM.get_channel(mark_video_watched_and_old.channel_id).name}" as watched.')


# @click.command('tui')
# def tui():
#     """ Open textual user interface (not for Windows). """
#     ytsm_tui.YTSMTui(ytsm=YTSM, settings=settings.Settings())


# @click.command('gui')
# def gui():
#     """ Open graphical user interface. """
#     ytsm_gui.App(ytsm=YTSM)

#######################################################################################################################


if __name__ == '__main__':
    ytsm.add_command(factory_restore)
    ytsm.add_command(notify_update)
    ytsm.add_command(list_channels)
    ytsm.add_command(add_channel)
    ytsm.add_command(remove_channel)
    ytsm.add_command(update_channel)
    ytsm.add_command(visit_channel)
    ytsm.add_command(find)
    ytsm.add_command(list_videos)
    ytsm.add_command(video_detail)
    ytsm.add_command(watch_video)
    ytsm.add_command(mark_watched)
    # ytsm.add_command(tui)
    # ytsm.add_command(gui)
    ytsm()
