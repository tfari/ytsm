""" CRUD Interface for accessing the repository and scraper"""
from typing import Optional

from ytsm.repository.sqlite_repository import AbstractRepository
from ytsm.scraper.yt_scraper import YTScraper
from ytsm.model import Channel, Video


class YTSubManager:
    """ Main interface for using the application, specifically the db and scraper. """
    def __init__(self, *, repository: AbstractRepository):
        self.repository = repository
        self.scraper = YTScraper()

    def add_channel(self, url: str) -> str:
        """
        Add a new channel via its URL, accepted URLs are /channel, /watch , /user, /c, and @ urls

        :raises ScraperError: if Scrapper has any error
        :raises ChannelAlreadyExists: if Channel with channel_id already exists in the database
        :raises ChannelDoesNotExist: if Channel with channel_id does not exist in the database -> Weird error,
        shouldn't happen, but it is a possible raise expected from the update_channel method.

        :return channel_id
        """
        # 1 - Get channel ID
        try:
            channel_id, thumbnail_url = self.scraper.get_channel_id_and_thumbnail_from_url(url)
        except self.scraper.YTScraperError as e:
            raise self.ScraperError(f'Error getting channel id and thumbnail: {e.__class__.__name__} - "{str(e)}"')

        # 2 - Check if channel already exists
        try:
            self.get_channel(channel_id)  # If it doesn't exist it should raise ChannelDoesNotExist
            raise self.ChannelAlreadyExists(f'Channel already exists: {self.get_channel(channel_id).name}')
        except self.ChannelDoesNotExist:
            pass

        # 3 - Get channel information
        try:
            channel_info = self.scraper.get_channel_information(channel_id)
        except self.scraper.YTScraperError as e:
            raise self.ScraperError(f'Error getting channel information: {str(type(e))} - {channel_id}')
        # 4 - Create channel
        self._add_channel(channel_info['id'], channel_info['name'], channel_info['url'], thumbnail_url)
        # 5 - Update channel
        self.update_channel(channel_id, use_cache=True)

        return channel_id

    def update_channel(self, channel_id: str, use_cache: bool = False) -> int:
        """
        Update a Channel by scraping and adding the new Videos if any

        :raises ScraperError: if Scrapper has any error
        :raises ChannelDoesNotExist: if Channel with channel_id does not exist in the database

        :return int, the number of new videos
        """
        try:
            videos = self.scraper.get_video_list(channel_id, use_cache=use_cache)
        except self.scraper.YTScraperError as e:
            raise self.ScraperError(f'Error getting video list: {str(type(e))} - {str(e)}')
        else:
            return self._update_video_list(videos, channel_id)

    def update_all_channels(self) -> dict[str, int]:
        """
        Update all Channels by scraping and adding the new Videos if any. Uses parallel scraping.

        :raises ScraperError: if Scrapper has any error
        :raises ChannelDoesNotExist: if Channel with channel_id does not exist in the database

        :return dict, {'total': total_new, 'channel_id': amt} -> Only Channel's that have new videos.
        """
        try:
            response = self.scraper.get_video_list_multiple([c.idx for c in self.get_all_channels()])
        except self.scraper.YTScraperError as e:
            raise self.ScraperError(f'Error getting all video lists: {str(type(e))}  - {str(e)}')
        else:
            response_dict = {'total': 0}
            for response_key in response.keys():
                amt = self._update_video_list(response[response_key], response_key)
                response_dict['total'] += amt
                if amt > 0:
                    response_dict[response_key] = amt
            return response_dict

    def _update_video_list(self, videos_dict_list: list[dict], channel_id: str) -> int:
        """
        Update a list of Videos on Channel with channel_id by adding all videos until we meet the last video uploaded
        to the Channel.

        :raises ChannelDoesNotExist: if Channel with channel_id does not exist in the database
        :return int, number of new Videos
        """
        try:
            last_video: Optional[Video] = self.repository.get_last_video_from_channel(channel_id)
        except self.repository.ObjectDoesNotExist:
            raise self.ChannelDoesNotExist(channel_id)

        num_new_videos = 0
        if last_video:
            for video in videos_dict_list:
                if video['id'] != last_video.idx:
                    try:
                        self._add_video(video['id'], video['channel_id'], video['name'], video['url'], video['pubdate'],
                                        video['description'], video['thumbnail'], deferred_commit=True)
                        num_new_videos += 1
                    except self.VideoAlreadyExists:
                        pass

                else:
                    break
        else:  # No videos
            for video in videos_dict_list:
                self._add_video(video['id'], video['channel_id'], video['name'], video['url'], video['pubdate'],
                                video['description'], video['thumbnail'], deferred_commit=True)
                num_new_videos += 1

        self.repository.call_commit()  # Commit changes
        return num_new_videos

    def _get_last_video_from_channel(self, channel_id: str) -> Optional[Video]:
        """
        Get last Video from Channel with channel_id, based on published date
        :raises ChannelDoesNotExist: if Channel with channel_id does not exist in the database
        """
        try:
            return self.repository.get_last_video_from_channel(channel_id)
        except self.repository.ObjectDoesNotExist:
            raise self.ChannelDoesNotExist(channel_id)

    def _add_channel(self, channel_id: str, channel_name: str, channel_url: str, thumbnail_url: str) -> None:
        """
        Add Channel to DB
        :raise ChannelAlreadyExists(channel_id)
        """
        try:
            self.repository.add_channel(channel_id, channel_name, channel_url, thumbnail_url)
        except AbstractRepository.ObjectAlreadyExists:
            raise self.ChannelAlreadyExists(channel_id)

    def get_channel(self, channel_id: str) -> Channel:
        """
        Get Channel from DB
        :raise ChannelDoesNotExist(channel_id)
        """
        try:
            return self.repository.get_channel(channel_id)
        except AbstractRepository.ObjectDoesNotExist:
            raise self.ChannelDoesNotExist(channel_id)

    def remove_channel(self, channel_id: str) -> None:
        """  Remove Channel from DB  """
        self.repository.remove_channel(channel_id)

    def find_channels(self, name_str: str) -> list[Channel]:
        """ Find Channels which names contain name_str, case-insensitive"""
        return self.repository.find_channels(name_str)

    def get_all_channels(self) -> list[Channel]:
        """ Get all the Channels from the database """
        return self.repository.get_all_channels()

    def _add_video(self, video_id: str, channel_id: str, video_name: str, video_url: str, video_pubdate: str,
                   video_description: str, video_thumbnail: str, *, deferred_commit: bool = False) -> None:
        """
        Add a Video to the database
        :raises ChannelDoesNotExist: if Channel with channel_id does not exist in the database
        :raises VideoAlreadyExists: if there is already a Video with video_id
        """
        try:
            # Added Videos are always New and Unwatched.
            self.repository.add_video(video_id, channel_id, video_name, video_url, video_pubdate, video_description,
                                      video_thumbnail, True, False, deferred_commit=deferred_commit)
        except AbstractRepository.ObjectAlreadyExists:
            raise self.VideoAlreadyExists(video_id)
        except AbstractRepository.ObjectDoesNotExist:
            raise self.ChannelDoesNotExist(channel_id)

    def get_video(self, video_id: str) -> Video:
        """
        Get a Video from the database
        :raises VideoDoesNotExist: if there is no Video with video_id
        """
        try:
            return self.repository.get_video(video_id)
        except AbstractRepository.ObjectDoesNotExist:
            raise self.VideoDoesNotExist(video_id)

    def find_video_by_name(self, name_str: str, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Find Videos which names contain name_str, case-insensitive. Optionally look only inside a specific
        Channel """
        return self.repository.find_video_by_key(name_str, channel_id=channel_id)

    def find_video_by_desc(self, desc_str: str, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Find Videos which desc contain desc_str, case-insensitive. Optionally look only inside a specific
        Channel """
        return self.repository.find_video_by_key(desc_str, desc=True, channel_id=channel_id)

    def get_all_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database. Optionally look only inside a specific Channel """
        return self.repository.get_all_videos(channel_id=channel_id)

    def mark_video_as_old(self, video_id: str) -> None:
        """ Edit Video with video_id to new=False """
        self.repository.mark_video_as_old(video_id)

    def mark_all_videos_old(self, channel_id: str) -> None:
        """ Edit all Videos in a Channel to new=False """
        self.repository.mark_all_videos_old(channel_id)

    def mark_video_as_watched(self, video_id: str) -> None:
        """ Edit Video with video_id to watched=False """
        self.repository.mark_video_as_watched(video_id)

    def mark_all_videos_watched(self, channel_id: str) -> None:
        """Edit all Videos in a Channel to watched=True """
        self.repository.mark_all_videos_watched(channel_id)

    def get_all_new_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have new=True. Optionally look only inside a specific Channel """
        return self.repository.get_all_new_videos(channel_id=channel_id)

    def get_all_unwatched_videos(self, *, channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have watched=False. Optionally look only inside a specific
        Channel """
        return self.repository.get_all_unwatched_videos(channel_id=channel_id)

    def get_all_videos_by_date_range(self, date_min: str, date_max: str, *,
                                     channel_id: Optional[str] = None) -> list[Video]:
        """ Get all the Videos from the database that have date_min < pubdate < date_max. Optionally look only inside a
        specific Channel """
        return self.repository.get_all_videos_by_date_range(date_min, date_max, channel_id=channel_id)

    def get_amt_videos(self, channel_id: str) -> tuple[int, int, int]:
        """
        Return a tuple of the following counts for Channel with channel_id: (all videos, new videos, unwatched videos)
        """
        return (self.repository.amt_channel_videos(channel_id=channel_id),
                self.repository.amt_channel_videos(channel_id=channel_id, video_type='new'),
                self.repository.amt_channel_videos(channel_id=channel_id, video_type='unwatched'))

    def _remove_video(self, video_id: str) -> None:
        """
        Remove a Video from the database
        """
        self.repository._remove_video(video_id)

    def set_notify_on_status_false(self, channel_id: str):
        """ Set Channel with channel_id to NOT notify on updates """
        self.repository.set_channel_notify_on_status(channel_id, False)

    def set_notify_on_status_true(self, channel_id: str):
        """ Set Channel with channel_id to notify on updates """
        self.repository.set_channel_notify_on_status(channel_id, True)

    class BaseYTSMError(Exception):
        """ Base class for YTSM errors """

    class ScraperError(BaseYTSMError):
        """ YTScraper raised an Exception """

    class ChannelAlreadyExists(BaseYTSMError):
        """ Attempted to add a Channel that already exists """

    class ChannelDoesNotExist(BaseYTSMError):
        """ Attempted to access a Channel that does not exist """

    class VideoAlreadyExists(BaseYTSMError):
        """ Attempted to add a Video that already exists """

    class VideoDoesNotExist(BaseYTSMError):
        """ Attempted to access a Video that does not exist """
