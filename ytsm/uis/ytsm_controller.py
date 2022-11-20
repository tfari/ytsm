""" Controller for using YTSubManager """
from __future__ import annotations

import dataclasses
import webbrowser

from ytsm.ytsubmanager import YTSubManager
from ytsm.model import Channel, Video


class YTSMController:
    """ Controller for YTSM UIs """
    ALL, NEW, UNWATCHED = 'ALL', 'NEW', 'UNWATCHED'  # Filter modes
    NAME, DESC, DATE = 'NAME', 'DESC', 'DATE'  # Video search modes

    def __init__(self, ytsm: YTSubManager):
        self.ytsm = ytsm
        self.video_filter = YTSMController.ALL
        self.video_search_type = YTSMController.NAME

        self.channel_search_term = ''
        self.video_search_term = ''

    def get_channel_dto_from_id(self, channel_id: str) -> ChannelDTO:
        """
        Get a ChannelDTO from a channel's id
        :raises ChannelDoesNotExist : If Channel with channel_id does not exist
        """
        try:
            return self.make_channel_dto(self.ytsm.get_channel(channel_id))
        except YTSubManager.ChannelDoesNotExist:
            raise self.ChannelIDNotFound(channel_id)

    def make_channel_dto(self, channel: Channel) -> ChannelDTO:
        """ Make a Channel DTO from a Channel """
        total, new, unwatched = self.ytsm.get_amt_videos(channel_id=channel.idx)
        return YTSMController.ChannelDTO(channel=channel, total=total, new=new, unwatched=unwatched)

    def make_video_dto(self, video: Video) -> VideoDTO:
        """ Make a Video DTO from a Video """
        return YTSMController.VideoDTO(video=video, channel_name=self.ytsm.get_channel(video.channel_id).name)

    def get_channel_dto_list(self) -> list[ChannelDTO]:
        """
        Get a list of ChannelDTO objects.
        Either returns all channels, or performs a search for self.channel_search_term, if it has been set.
        """
        if self.channel_search_term:
            channel_list = self.ytsm.find_channels(name_str=self.channel_search_term)
        else:
            channel_list = self.ytsm.get_all_channels()

        return sorted([self.make_channel_dto(c) for c in channel_list], key=lambda cdto: cdto.channel.name.upper())

    def get_video_dto_list(self, channel_id: str, *, all_videos: bool = False) -> list[VideoDTO]:
        """
        Get a list of VideoDTO objects, either by channel_id or all of them by passing all_videos=True
        If self.video_filter, or a self.video_search_type and self.video_search_term has been altered, return after
        performing a search, filter, or both.
        """
        # Search terms
        if all_videos:
            channel_id = None

        video_list = []
        if self.video_search_term:
            if self.video_search_type == YTSMController.NAME:
                video_list = self.ytsm.find_video_by_name(name_str=self.video_search_term, channel_id=channel_id)
            elif self.video_search_type == YTSMController.DESC:
                video_list = self.ytsm.find_video_by_desc(desc_str=self.video_search_term, channel_id=channel_id)
            elif self.video_search_type == YTSMController.DATE:
                try:
                    date_min, date_max = self.video_search_term.split(' ')
                    video_list = self.ytsm.get_all_videos_by_date_range(date_min, date_max, channel_id=channel_id)
                except ValueError:
                    video_list = []
        else:
            video_list = self.ytsm.get_all_videos(channel_id=channel_id)

        # Filter # TODO: YTSubManager, a way to search by term + filter?
        video_dto_list = [self.make_video_dto(v) for v in video_list]
        if self.video_filter == YTSMController.NEW:
            video_dto_list = filter(lambda v_dto: v_dto.video.new, video_dto_list)
        elif self.video_filter == YTSMController.UNWATCHED:
            video_dto_list = filter(lambda v_dto: not v_dto.video.watched, video_dto_list)

        # Mark videos as old if not all_videos call (channel is being visited)
        if not all_videos:
            self.ytsm.mark_all_videos_old(channel_id=channel_id)

        # Order
        return sorted(video_dto_list, key=lambda vdto: vdto.video.pubdate, reverse=True)

    def set_channel_search_term(self, channel_search_terms: str) -> None:
        """ Change the search terms for Channels in order to search by name when requesting data. """
        self.channel_search_term = channel_search_terms

    def set_video_filter(self, new_video_filter: str) -> None:
        """
        Change the Video filter in order to search by name when requesting data.
        :raises ValueError: if new_video_filter not YTSMController.ALL, YTSMController.NEW or YTRSMController.UNWATCHED
        """
        if new_video_filter not in (YTSMController.ALL, YTSMController.NEW, YTSMController.UNWATCHED):
            raise ValueError('Filter must be one of YTSMController.ALL, YTSMController.NEW, '
                             'or YTSMController.UNWATCHED')
        else:
            self.video_filter = new_video_filter

    def set_video_search_term(self, video_search_terms: str) -> None:
        """ Change the search terms for searching Videos when requesting data. """
        self.video_search_term = video_search_terms

    def set_video_search_type(self, new_search_type: str) -> None:
        """
        Change the search type for searching Videos when requesting data.
        :raises ValueError: if new_search_type not YTSMController.NAME, YTSMController.DESC or YTRSMController.DATE
        """
        if new_search_type not in (YTSMController.NAME, YTSMController.DESC, YTSMController.DATE):
            raise ValueError('Filter must be one of YTSMController.NAME, YTSM.Controller.DESC, '
                             'or YTSMController.DATE')
        else:
            self.video_search_type = new_search_type

    def add_channel(self, url: str) -> Channel:
        """
        Add a Channel, returns it.
        :param url: valid YT channel/video url (/watch?v=, /channel, /user, /@)
        :raises AddChannelError: if the attempt to add a Channel failed
        """
        try:
            idx = self.ytsm.add_channel(url)
        except YTSubManager.BaseYTSMError as e:
            raise self.AddChannelError(f'{e.args[0]}')
        else:
            return self.ytsm.get_channel(idx)

    def remove_channel(self, channel_dto: ChannelDTO) -> None:
        """ Remove a Channel """
        self.ytsm.remove_channel(channel_dto.channel.idx)

    def mark_channel_all_watched(self, channel_dto: ChannelDTO) -> None:
        """ Mark all videos in a channel as watched """
        self.ytsm.mark_all_videos_watched(channel_dto.channel.idx)
        self.ytsm.mark_all_videos_old(channel_dto.channel.idx)

    def update_channel(self, channel_dto: ChannelDTO) -> int:
        """
        Update a Channel, return the amount of new videos.
        :raises UpdateChannelError: if the attempt to update a Channel failed
        """
        try:
            amt = self.ytsm.update_channel(channel_dto.channel.idx)
        except YTSubManager.BaseYTSMError as e:
            raise YTSMController.UpdateChannelError(f'{e}')
        return amt

    def update_all_channels(self) -> dict:
        """
        Update all Channels, return the total amount of new videos, and the amount per channel name, as a list of
        tuples under the key "details".
        :raises UpdateAllChannelsError: if the attempt to update all channels failed
        :return : dict -> {'total': 2, 'details': [('channel_name', 1), ('channel_name', 1)]}
        """
        try:
            update_data = self.ytsm.update_all_channels()
        except YTSubManager.BaseYTSMError as e:
            raise YTSMController.UpdateAllChannelsError(f'{e}')
        else:
            response = {'total': update_data['total'], 'details': [], 'errs': update_data['errs']}
            for ud_key in update_data['new']:
                if ud_key != "total":
                    response['details'].append((self.ytsm.get_channel(ud_key).name, update_data['new'][ud_key]))

            return response

    def mark_video_watched(self, video_dto: VideoDTO) -> None:
        """ Mark a Video as watched """
        self.ytsm.mark_video_as_watched(video_dto.video.idx)

    def watch_video(self, video_dto: VideoDTO) -> None:
        """ Watch a video """
        webbrowser.open(video_dto.video.url)
        self.mark_video_watched(video_dto)

    @staticmethod
    def visit_channel(channel_dto: ChannelDTO) -> None:
        """ Visit a Channel's YT page """
        webbrowser.open(channel_dto.channel.url)

    def toggle_mute_channel(self, channel_dto: ChannelDTO) -> None:
        """ Toggle Channel's notify_on status """
        if channel_dto.channel.notify_on:
            self.ytsm.set_notify_on_status_false(channel_dto.channel.idx)
        else:
            self.ytsm.set_notify_on_status_true(channel_dto.channel.idx)

    @dataclasses.dataclass
    class ChannelDTO:
        """ Data Transfer Objects for Channels """
        channel: Channel
        new: int
        unwatched: int
        total: int

    @dataclasses.dataclass
    class VideoDTO:
        """ Data Transfer Objects for Videos """
        video: Video
        channel_name: str

    class AddChannelError(Exception):
        """ Attempted Channel add generated an error """

    class ChannelIDNotFound(Exception):
        """ Channel ID was not found """

    class UpdateChannelError(Exception):
        """ Attempted Channel update generated an error """

    class UpdateAllChannelsError(Exception):
        """ Attempted all Channels update generated an error """
