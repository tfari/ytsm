""" Repository classes """
import sqlite3
from abc import ABCMeta, abstractmethod
from typing import Optional

from ytsm.model import Channel, Video
from ytsm.settings import SETTINGS, SQLITE_DB_CREATION_STATEMENTS


class AbstractRepository(metaclass=ABCMeta):
    """ Abstract repository class """
    @abstractmethod
    def amt_channel_videos(self, channel_id: str, video_type: str = 'all') -> int:
        """
        Returns the amount of videos in Channel with channel_id, specified by video_type = 'all', 'new', 'unwatched'
        """

    @abstractmethod
    def add_channel(self, channel_id: str, channel_name: str, channel_uri: str) -> None:
        """
        Add a Channel to the database
        :raises ObjectAlreadyExist: if there is already a Channel with channel_id
        """

    @abstractmethod
    def get_channel(self, channel_id: str) -> Channel:
        """
        Get a Channel from the database
        :raises ObjectDoesNotExist: if there is no Channel with channel_id
        """

    @abstractmethod
    def remove_channel(self, channel_id: str) -> None:
        """ Remove a Channel from the database """

    @abstractmethod
    def find_channels(self, name_str: str) -> list[Channel]:
        """ Find Channels which names contain name_str, case-insensitive"""

    @abstractmethod
    def get_all_channels(self) -> list[Channel]:
        """ Get all the Channels from the database """

    @abstractmethod
    def add_video(self, video_id: str, channel_id: str, video_name: str, video_url: str, video_pubdate: str,
                  video_description: str, video_thumbnail: str, video_new: bool, video_watched: bool) -> None:
        """
        Add a Video to the database, if we are on the SETTINGS limit for max videos, make place for it.
        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        :raises ObjectAlreadyExist: if there is already a Video with video_id
        """

    @abstractmethod
    def _remove_video(self, video_id: str):
        """
        Remove a Video from the database
        """

    @abstractmethod
    def get_video(self, video_id: str) -> Video:
        """
        Get a Video from the database
        :raises ObjectDoesNotExist: if there is no Video with video_id
        """

    @abstractmethod
    def find_video_by_key(self, find_str: str, *, desc: bool = False, channel_id: Optional[str] = None) -> list[Video]:
        """ Find Videos which names (or desc if desk is True) contains find_str, case-insensitive. Optionally look only
        inside a specific Channel """

    @abstractmethod
    def get_all_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database. Optionally look only inside a specific Channel """

    @abstractmethod
    def mark_video_as_old(self, video_id: str) -> None:
        """ Edit Video with video_id to new=False """

    @abstractmethod
    def mark_all_videos_old(self, channel_id: str) -> None:
        """ Edit all Videos in a Channel to new=False """

    @abstractmethod
    def mark_video_as_watched(self, video_id: str) -> None:
        """ Edit Video with video_id to watched=True """

    @abstractmethod
    def mark_all_videos_watched(self, channel_id: str) -> None:
        """ Edit all Videos in a Channel to watched=True """

    @abstractmethod
    def get_all_new_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have new=True. Optionally look only inside a specific Channel """

    @abstractmethod
    def get_all_unwatched_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have watched=False. Optionally look only inside a specific
        Channel """

    @abstractmethod
    def get_all_videos_by_date_range(self, date_min: str, date_max: str, *,
                                     channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have date_min < pubdate < date_max. Optionally look only inside a
        specific Channel """

    @abstractmethod
    def get_last_video_from_channel(self, channel_id: str) -> Optional[Video]:
        """
        Get last Video from Channel with channel_id, based on published date
        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        """

    def get_oldest_video_from_channel(self, channel_id: str) -> Optional[Video]:
        """
        Get the oldest Video from Channel with channel_id, based on published date
        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        """

    class BaseRepositoryError(Exception):
        """ Base class for Repository errors """

    class ObjectAlreadyExists(Exception):
        """ Attempted to add to the database an object that already exists """

    class ObjectDoesNotExist(Exception):
        """ Attempted to access an object that does not exist """


class SQLiteRepository(AbstractRepository):
    """ SQLite Repository implementation"""

    def __init__(self, db_path: str):
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

        self.cur.execute("PRAGMA foreign_keys=on")  # Ensure we are using foreign_keys
        self.con.commit()

    @staticmethod
    def create_db(db_path: str):
        """ Creates the DB on db_path """
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        for sqlite_statement in SQLITE_DB_CREATION_STATEMENTS:
            cur.execute(sqlite_statement)
        con.commit()
        con.close()

    def amt_channel_videos(self, channel_id: str, video_type: str = 'all') -> int:
        """ Returns the amount of videos in Channel with channel_id, specified by video_type = 'all', 'new',
        'unwatched' """
        curs = {'all': 'SELECT COUNT() FROM videos WHERE channel_id=?',
                'new': 'SELECT COUNT() FROM videos WHERE channel_id=? AND new=TRUE',
                'unwatched': 'SELECT COUNT() FROM videos WHERE channel_id=? AND watched=FALSE'}
        self.cur.execute(curs[video_type], (channel_id,))
        found = self.cur.fetchone()[0]
        return found

    def add_channel(self, channel_id: str, channel_name: str, channel_url: str) -> None:
        """
        Add a Channel to the database
        :raises ObjectAlreadyExist: if there is already a Channel with channel_id
        """
        try:
            self.cur.execute('INSERT into channels values(?, ?, ?)', (channel_id, channel_name, channel_url))
            self.con.commit()
        except sqlite3.IntegrityError:
            raise self.ObjectAlreadyExists(channel_id)

    def get_channel(self, channel_id: str) -> Channel:
        """
        Get a Channel from the database
        :raises ObjectDoesNotExist: if there is no Channel with channel_id
        """
        self.cur.execute('SELECT * FROM channels WHERE id=?', (channel_id,))
        found = self.cur.fetchone()
        if not found:
            raise self.ObjectDoesNotExist(channel_id)
        return Channel(found[0], found[1], found[2])

    def remove_channel(self, channel_id: str) -> None:
        """ Remove a Channel from the database """
        self.cur.execute('DELETE FROM channels WHERE id=?', (channel_id,))
        self.con.commit()

    def find_channels(self, name_str: str) -> list[Channel]:
        """ Find Channels which names contain name_str, case-insensitive"""
        self.cur.execute('SELECT * FROM channels WHERE UPPER(name) LIKE ?', (f'%{name_str.upper()}%',))
        found = self.cur.fetchall()
        return [Channel(f[0], f[1], f[2]) for f in found]

    def get_all_channels(self) -> list[Channel]:
        """ Get all the Channels from the database """
        self.cur.execute('SELECT * FROM channels')
        found = self.cur.fetchall()
        return [Channel(f[0], f[1], f[2]) for f in found]

    def add_video(self, video_id: str, channel_id: str, video_name: str, video_url: str, video_pubdate: str,
                  video_description: str, video_thumbnail: str, video_new: bool, video_watched: bool) -> None:
        """
        Add a Video to the database, if we are on the SETTINGS limit for max videos, make place for it.

        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        :raises ObjectAlreadyExist: if there is already a Video with video_id
        """
        # Delete older videos if appropriate
        amt_videos = self.amt_channel_videos(channel_id)
        if amt_videos == SETTINGS.advanced_settings.max_videos_per_channel:
            v = self.get_oldest_video_from_channel(channel_id)
            self._remove_video(v.idx)

        # Insert new video
        try:
            self.cur.execute('INSERT into videos values(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (video_id, channel_id, video_name, video_url, video_pubdate, video_description,
                              video_thumbnail, video_new, video_watched))
            self.con.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                raise self.ObjectAlreadyExists(video_id)
            elif "FOREIGN KEY" in str(e):
                raise self.ObjectDoesNotExist(channel_id)

    def _remove_video(self, video_id: str):
        """
        Remove a Video from the database
        """
        self.cur.execute('DELETE FROM videos WHERE id=?', (video_id,))
        self.con.commit()

    def get_video(self, video_id: str) -> Video:
        """
        Get a Video from the database
        :raises ObjectDoesNotExist: if there is no Video with video_id
        """
        self.cur.execute('SELECT * FROM videos WHERE id=?', (video_id,))
        found = self.cur.fetchone()
        if not found:
            raise self.ObjectDoesNotExist(video_id)
        return Video(found[0], found[1], found[2], found[3], found[4], found[5], found[6], found[7], found[8])

    def find_video_by_key(self, find_str: str, *, desc: bool = False, channel_id: Optional[str] = None) -> list[Video]:
        """ Find Videos which names (or desc if desk is True) contains find_str, case-insensitive. Optionally look only
        inside a specific Channel """
        if not channel_id:
            if not desc:
                self.cur.execute('SELECT * FROM videos WHERE UPPER(name) LIKE ?', (f'%{find_str.upper()}%',))
            else:
                self.cur.execute('SELECT * FROM videos WHERE UPPER(description) LIKE ?', (f'%{find_str.upper()}%',))
        else:
            if not desc:
                self.cur.execute('SELECT * FROM videos WHERE UPPER(name) LIKE ? AND channel_id=?',
                                 (f'%{find_str.upper()}%', channel_id))
            else:
                self.cur.execute('SELECT * FROM videos WHERE UPPER(description) LIKE ? AND channel_id=?',
                                 (f'%{find_str.upper()}%', channel_id))

        found = self.cur.fetchall()
        return [Video(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8]) for f in found]

    def get_all_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database. Optionally look only inside a specific Channel """
        if not channel_id:
            self.cur.execute('SELECT * FROM videos')
        else:
            self.cur.execute('SELECT * FROM videos WHERE channel_id=?', (channel_id,))

        found = self.cur.fetchall()
        return [Video(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8]) for f in found]

    def mark_video_as_old(self, video_id: str) -> None:
        """ Edit Video with video_id to new=False """
        self.cur.execute('UPDATE videos SET new=FALSE WHERE id=?', (video_id,))
        self.con.commit()

    def mark_all_videos_old(self, channel_id: str) -> None:
        """ Edit all Videos in a Channel to new=False """
        self.cur.execute('UPDATE videos SET new=FALSE WHERE channel_id=?', (channel_id,))
        self.con.commit()

    def mark_video_as_watched(self, video_id: str) -> None:
        """ Edit Video with video_id to watched=True """
        self.cur.execute('UPDATE videos SET watched=TRUE WHERE id=?', (video_id,))
        self.con.commit()

    def mark_all_videos_watched(self, channel_id: str) -> None:
        """ Edit all Videos in a Channel to watched=True """
        self.cur.execute('UPDATE videos SET watched=TRUE WHERE channel_id=?', (channel_id,))
        self.con.commit()

    def get_all_new_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have new=True. Optionally look only inside a specific Channel """
        if not channel_id:
            self.cur.execute('SELECT * FROM videos WHERE new=TRUE')
        else:
            self.cur.execute('SELECT * FROM videos WHERE new=TRUE AND channel_id=?', (channel_id,))

        found = self.cur.fetchall()
        return [Video(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8]) for f in found]

    def get_all_unwatched_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have watched=False. Optionally look only inside a specific
        Channel """
        if not channel_id:
            self.cur.execute('SELECT * FROM videos WHERE watched=FALSE')
        else:
            self.cur.execute('SELECT * FROM videos WHERE watched=FALSE AND channel_id=?', (channel_id,))

        found = self.cur.fetchall()
        return [Video(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8]) for f in found]

    def get_all_videos_by_date_range(self, date_min: str, date_max: str, *,
                                     channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have date_min < pubdate < date_max. Optionally look only inside a
        specific Channel """
        if not channel_id:
            self.cur.execute('SELECT * FROM videos WHERE pubdate > ? AND pubdate < ?', (date_min, date_max))
        else:
            self.cur.execute('SELECT * FROM videos WHERE pubdate > ? AND pubdate < ? AND channel_id=?',
                             (date_min, date_max, channel_id))

        found = self.cur.fetchall()
        return [Video(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8]) for f in found]

    def get_last_video_from_channel(self, channel_id: str) -> Optional[Video]:
        """
        Get last Video from Channel with channel_id, based on published date
        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        """
        self.get_channel(channel_id)
        self.cur.execute('SELECT * FROM videos WHERE channel_id=? ORDER BY pubdate DESC', (channel_id,))
        found = self.cur.fetchone()
        if not found:
            return None
        return Video(found[0], found[1], found[2], found[3], found[4], found[5], found[6], found[7], found[8])

    def get_oldest_video_from_channel(self, channel_id: str) -> Optional[Video]:
        """
        Get the oldest Video from Channel with channel_id, based on published date
        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        """
        self.get_channel(channel_id)
        self.cur.execute('SELECT * FROM videos WHERE channel_id=? ORDER BY pubdate ASC', (channel_id,))
        found = self.cur.fetchone()
        if not found:
            return None
        return Video(found[0], found[1], found[2], found[3], found[4], found[5], found[6], found[7], found[8])
