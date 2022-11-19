""" SQLite Repository """
import sqlite3
from ytsm.repository.abstract_repository import AbstractRepository

from typing import Optional

from ytsm.model import Channel, Video
from ytsm.settings import SETTINGS, SQLITE_DB_CREATION_STATEMENTS


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

    def _get_all_channel_keys(self) -> list[str]:
        self.cur.execute("SELECT id FROM channels")
        return [t[0] for t in self.cur.fetchall()]

    def _get_all_videos_keys(self) -> list[str]:
        self.cur.execute("SELECT id FROM videos")
        return [t[0] for t in self.cur.fetchall()]

    def call_commit(self) -> None:
        """ Calls a commit on the DB """
        self.con.commit()

    def amt_channel_videos(self, channel_id: str, video_type: str = 'all') -> int:
        """ Returns the amount of videos in Channel with channel_id, specified by video_type = 'all', 'new',
        'unwatched' """
        curs = {'all': 'SELECT COUNT() FROM videos WHERE channel_id=?',
                'new': 'SELECT COUNT() FROM videos WHERE channel_id=? AND new=TRUE',
                'unwatched': 'SELECT COUNT() FROM videos WHERE channel_id=? AND watched=FALSE'}
        self.cur.execute(curs[video_type], (channel_id,))
        found = self.cur.fetchone()[0]
        return found

    def add_channel(self, channel_id: str, channel_name: str, channel_url: str, thumbnail_url: str) -> None:
        """
        Add a Channel to the database
        :raises ObjectAlreadyExist: if there is already a Channel with channel_id
        """
        try:
            self.cur.execute('INSERT into channels values(?, ?, ?, ?, ?)', (channel_id, channel_name, channel_url,
                                                                            True, thumbnail_url))
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
        return Channel(*found)

    def remove_channel(self, channel_id: str) -> None:
        """ Remove a Channel from the database """
        self.cur.execute('DELETE FROM channels WHERE id=?', (channel_id,))
        self.con.commit()

    def find_channels(self, name_str: str) -> list[Channel]:
        """ Find Channels which names contain name_str, case-insensitive"""
        self.cur.execute('SELECT * FROM channels WHERE UPPER(name) LIKE ?', (f'%{name_str.upper()}%',))
        found = self.cur.fetchall()
        return [Channel(*f) for f in found]

    def get_all_channels(self) -> list[Channel]:
        """ Get all the Channels from the database """
        self.cur.execute('SELECT * FROM channels')
        found = self.cur.fetchall()
        return [Channel(*f) for f in found]

    def add_video(self, video_id: str, channel_id: str, video_name: str, video_url: str, video_pubdate: str,
                  video_description: str, video_thumbnail: str, video_new: bool, video_watched: bool, *,
                  deferred_commit: bool = False) -> None:
        """
        Add a Video to the database, if we are on the SETTINGS limit for max videos, make place for it.
        If deferred_commit is true, don't call commit after adding the videos.

        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        :raises ObjectAlreadyExist: if there is already a Video with video_id
        """
        # Delete older videos if appropriate
        amt_videos = self.amt_channel_videos(channel_id)
        while amt_videos >= SETTINGS.advanced_settings.max_videos_per_channel:
            v = self.get_oldest_video_from_channel(channel_id)
            self._remove_video(v.idx)
            amt_videos -= 1

        # Insert new video
        try:
            self.cur.execute('INSERT into videos values(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (video_id, channel_id, video_name, video_url, video_pubdate, video_description,
                              video_thumbnail, video_new, video_watched))
            if not deferred_commit:
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
        return Video(*found)

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
        return [Video(*f) for f in found]

    def get_all_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database. Optionally look only inside a specific Channel """
        if not channel_id:
            self.cur.execute('SELECT * FROM videos')
        else:
            self.cur.execute('SELECT * FROM videos WHERE channel_id=?', (channel_id,))

        found = self.cur.fetchall()
        return [Video(*f) for f in found]

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
        return [Video(*f) for f in found]

    def get_all_unwatched_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have watched=False. Optionally look only inside a specific
        Channel """
        if not channel_id:
            self.cur.execute('SELECT * FROM videos WHERE watched=FALSE')
        else:
            self.cur.execute('SELECT * FROM videos WHERE watched=FALSE AND channel_id=?', (channel_id,))

        found = self.cur.fetchall()
        return [Video(*f) for f in found]

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
        return [Video(*f) for f in found]

    def get_last_video_from_channel(self, channel_id: str) -> Optional[Video]:
        """
        Get last Video from Channel with channel_id, based on published date
        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        """
        return self.__get_last_old_video(channel_id, 'DESC')

    def get_oldest_video_from_channel(self, channel_id: str) -> Optional[Video]:
        """
        Get the oldest Video from Channel with channel_id, based on published date
        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        """
        return self.__get_last_old_video(channel_id, 'ASC')

    def __get_last_old_video(self, channel_id: str, order: str) -> Optional[Video]:
        """
        Get the oldest or latest Video from Channel with channel_id
        :param order: str = ASC/DESC
        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        """
        self.get_channel(channel_id)
        self.cur.execute(f'SELECT * FROM videos WHERE channel_id=? ORDER BY pubdate {order}', (channel_id,))
        found = self.cur.fetchone()
        return Video(*found) if found else None

    def set_channel_notify_on_status(self, channel_id: str, notify_status: bool) -> None:
        """ Set the Channel with channel_id's notify_on to notify_status """
        self.cur.execute('UPDATE channels SET notify_on=? WHERE id=?', (notify_status, channel_id,))
        self.con.commit()
