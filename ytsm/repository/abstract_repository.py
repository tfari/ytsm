""" Abstract Repository """
from typing import Optional
from abc import ABCMeta, abstractmethod

from ytsm.model import Channel, Video


class AbstractRepository(metaclass=ABCMeta):
    """ Abstract repository class """
    @abstractmethod
    def call_commit(self) -> None:
        """ Calls a commit on the DB """

    @abstractmethod
    def amt_channel_videos(self, channel_id: str, video_type: str = 'all') -> int:
        """
        Returns the amount of videos in Channel with channel_id, specified by video_type = 'all', 'new', 'unwatched'
        """

    @abstractmethod
    def add_channel(self, channel_id: str, channel_name: str, channel_uri: str, thumbnail_url: str) -> None:
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
                  video_description: str, video_thumbnail: str, video_new: bool, video_watched: bool, *,
                  deferred_commit: bool = False) -> None:
        """
        Add a Video to the database, if we are on the SETTINGS limit for max videos, make place for it.
        If deferred_commit is true, don't call commit after adding the videos.

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

    @abstractmethod
    def get_oldest_video_from_channel(self, channel_id: str) -> Optional[Video]:
        """
        Get the oldest Video from Channel with channel_id, based on published date
        :raises ObjectDoesNotExist: if Channel with channel_id does not exist in the database
        """

    @abstractmethod
    def set_channel_notify_on_status(self, channel_id: str, notify_status: bool) -> None:
        """ Set the Channel with channel_id's notify_on to notify_status """

    class BaseRepositoryError(Exception):
        """ Base class for Repository errors """

    class ObjectAlreadyExists(Exception):
        """ Attempted to add to the database an object that already exists """

    class ObjectDoesNotExist(Exception):
        """ Attempted to access an object that does not exist """
