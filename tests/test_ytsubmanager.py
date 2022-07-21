""" Tests for YTSubManager """
from unittest import TestCase
from ytsm.ytsubmanager import YTSubManager, YTScraper
from ytsm.repository import SQLiteRepository
from ytsm.model import Channel, Video


class TestYTSubManager(TestCase):
    @staticmethod
    def _raiser_helper(ex):
        """ Monkey patch raises """
        raise ex

    def setUp(self) -> None:
        """ Set up DB in memory """
        repo = SQLiteRepository(db_path=':memory:')
        repo.cur.execute(
            """
            CREATE TABLE channels (
                    id   TEXT PRIMARY KEY NOT NULL,
                    name TEXT NOT NULL,
                    url  TEXT NOT NULL
            );
            """
        )
        repo.cur.execute(
            """
            CREATE TABLE videos (
                id          TEXT     PRIMARY KEY ON CONFLICT FAIL
                                     NOT NULL,
                channel_id  TEXT     REFERENCES channels (id) ON DELETE CASCADE
                                     NOT NULL,
                name        TEXT     NOT NULL,
                url         TEXT     NOT NULL,
                pubdate     DATETIME NOT NULL,
                description TEXT     NOT NULL,
                thumbnail   TEXT     NOT NULL,
                new         BOOLEAN  NOT NULL,
                watched     BOOLEAN  NOT NULL
            );
            """
        )
        self.ytsm: YTSubManager = YTSubManager(repository=repo)

    def test_add_channel(self):
        # Just check everything goes around
        self.ytsm.scraper.get_channel_id_from_url = lambda x: '777'
        self.ytsm.scraper.get_channel_information = lambda x: {'id': '777', 'name': '777', 'url': '777'}
        self.ytsm.scraper.cache = {'777': ''}
        self.ytsm.scraper.update_channel = lambda x, use_cache: '777'
        self.assertEqual('777', self.ytsm.add_channel('test'))

    def test_add_channel_raises_ScraperError_on_YTScraper_errors(self):
        self.ytsm.scraper.get_channel_id_from_url = lambda x: self._raiser_helper(YTScraper.UrlNotYT)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')
        self.ytsm.scraper.get_channel_id_from_url = lambda x: self._raiser_helper(YTScraper.YTUrlNotSupported)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')
        self.ytsm.scraper.get_channel_id_from_url = lambda x: self._raiser_helper(YTScraper.YTUrl404)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')
        self.ytsm.scraper.get_channel_id_from_url = lambda x: self._raiser_helper(YTScraper.YTUrlUnexpectedStatusCode)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')
        self.ytsm.scraper.get_channel_id_from_url = lambda x: self._raiser_helper(YTScraper.GettingError)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')
        self.ytsm.scraper.get_channel_id_from_url = lambda x: self._raiser_helper(YTScraper.ChannelIDParsingError)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')

        self.ytsm.scraper.get_channel_id_from_url = lambda x: 'test'

        self.ytsm.scraper.get_channel_information = lambda x: self._raiser_helper(YTScraper.YTUrl404)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')
        self.ytsm.scraper.get_channel_information = lambda x: self._raiser_helper(YTScraper.YTUrlUnexpectedStatusCode)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')
        self.ytsm.scraper.get_channel_information = lambda x: self._raiser_helper(YTScraper.GettingError)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')
        self.ytsm.scraper.get_channel_information = lambda x: self._raiser_helper(YTScraper.ChannelInfoParsingError)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')

        # Also funnels ScraperErrors from update_channel
        self.ytsm.scraper.get_channel_information = lambda x: {'id': '666', 'name': '666', 'url': '666'}
        self.ytsm.update_channel = lambda x, use_cache: self._raiser_helper(YTSubManager.ScraperError)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.add_channel, '666')

    def test_add_channel_raises_ChannelAlreadyExists(self):
        self.ytsm._add_channel('test', '', '')
        self.ytsm.scraper.get_channel_id_from_url = lambda x: 'test'
        self.assertRaises(YTSubManager.ChannelAlreadyExists, self.ytsm.add_channel, '666')

    def test_add_channel_raises_ChannelDoesNotExist(self):
        """ This should never happen, as the Channel is created before the call to update_channel """
        self.ytsm.scraper.get_channel_id_from_url = lambda x: 'test'
        self.ytsm.scraper.get_channel_information = lambda x: {'id': 'test', 'name': 'name', 'url': 'url'}
        self.ytsm.update_channel = lambda x, use_cache: self._raiser_helper(YTSubManager.ChannelAlreadyExists)
        self.assertRaises(YTSubManager.ChannelAlreadyExists, self.ytsm.add_channel, '666')

    def test_update_channel(self):
        # Just check it funnels the result from _update_video_list
        self.ytsm.scraper.get_video_list = lambda x, use_cache: []
        self.ytsm._update_video_list = lambda x, y: 777
        self.assertEqual(777, self.ytsm.update_channel('test'))

    def test_update_channel_raises_ScraperError_on_YTScraper_errors(self):
        self.ytsm.scraper.get_video_list = lambda x, use_cache: self._raiser_helper(YTScraper.YTUrl404)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.update_channel, '666')
        self.ytsm.scraper.get_video_list = lambda x, use_cache: self._raiser_helper(YTScraper.YTUrlUnexpectedStatusCode)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.update_channel, '666')
        self.ytsm.scraper.get_video_list = lambda x, use_cache: self._raiser_helper(YTScraper.YTScraperError)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.update_channel, '666')

    def test_update_channel_raises_ChannelDoesNotExist(self):
        self.ytsm.scraper.get_video_list = lambda x, use_cache: []
        self.assertRaises(YTSubManager.ChannelDoesNotExist, self.ytsm.update_channel, '666')

    def test_update_all_channels(self):
        # Empty check
        self.ytsm.update_all_channels()
        # Just check it funnels the results from _update_video_list
        self.ytsm.scraper.get_video_list_multiple = lambda x: {'a': 'b', 'b': 'a'}
        self.ytsm._update_video_list = lambda x, y: 388.5  # cute
        self.assertEqual(777, self.ytsm.update_all_channels())

    def test_update_all_channels_raises_ScraperError_on_YTScraper_errors(self):
        self.ytsm.scraper.get_video_list_multiple = lambda x: self._raiser_helper(YTScraper.YTUrl404)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.update_all_channels)
        self.ytsm.scraper.get_video_list_multiple = lambda x: self._raiser_helper(
            YTScraper.YTUrlUnexpectedStatusCode)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.update_all_channels)
        self.ytsm.scraper.get_video_list_multiple = lambda x: self._raiser_helper(YTScraper.YTScraperError)
        self.assertRaises(YTSubManager.ScraperError, self.ytsm.update_all_channels)

    def test_update_all_channels_raises_ChannelDoesNotExist(self):
        self.ytsm.scraper.get_video_list_multiple = lambda x: {'666': [666]}
        self.assertRaises(YTSubManager.ChannelDoesNotExist, self.ytsm.update_all_channels)

    def test__update_video_list(self):
        # Set up
        self.ytsm._add_channel('1', '', '')
        self.ytsm._add_video('1', '1', '', '', '', '', '')

        # Existing video
        expected = 0
        self.assertEqual(expected, self.ytsm._update_video_list(
            [{'id': '1', 'channel_id': '1', 'name': '', 'url': '', 'pubdate': '', 'description': '', 'thumbnail': ''}],
            '1'))

        # New videos
        expected = 2
        self.assertEqual(expected, self.ytsm._update_video_list(
            [{'id': '3', 'channel_id': '1', 'name': '', 'url': '', 'pubdate': '', 'description': '', 'thumbnail': ''},
             {'id': '2', 'channel_id': '1', 'name': '', 'url': '', 'pubdate': '', 'description': '', 'thumbnail': ''},
             {'id': '1', 'channel_id': '1', 'name': '', 'url': '', 'pubdate': '', 'description': '', 'thumbnail': ''}],
            '1'))

    def test__update_video_list_raises_ChannelDoesNotExist(self):
        self.assertRaises(YTSubManager.ChannelDoesNotExist, self.ytsm._update_video_list,
                          [{}], '666')

    def test_get_last_video_from_channel(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.assertIsNone(self.ytsm._get_last_video_from_channel('test'))

        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test3', 'test', 'Name', 'Url', '22-02-03', 'Desc', 'Thumbnail')
        self.assertEqual(Video('test3', 'test', 'Name', 'Url', '22-02-03', 'Desc', 'Thumbnail', True, False),
                         self.ytsm._get_last_video_from_channel('test'))

    def test_get_last_video_from_channel_raises_ChannelDoesNotExist(self):
        self.assertRaises(YTSubManager.ChannelDoesNotExist, self.ytsm._get_last_video_from_channel, 'test')

    def test__add_channel(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.assertEqual(Channel('test', 'Name', 'URL'), self.ytsm.get_channel('test'))

    def test__add_channel_raises_ChannelAlreadyExists(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.assertRaises(YTSubManager.ChannelAlreadyExists, self.ytsm._add_channel, 'test', 'Name', 'URL')

    def test_get_channel(self):
        self.ytsm._add_channel('test', 'Channel Name', 'URL')
        self.assertEqual(Channel('test', 'Channel Name', 'URL'), self.ytsm.get_channel('test'))

    def test_get_channel_raises_ChannelDoesNotExist(self):
        self.assertRaises(YTSubManager.ChannelDoesNotExist, self.ytsm.get_channel, '666')

    def test_remove_channel(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm.remove_channel('test')
        self.assertRaises(YTSubManager.ChannelDoesNotExist, self.ytsm.get_channel, 'test')

    def test_find_channels(self):
        # Also check case-insensitive
        self.ytsm._add_channel('1', 'TEST', 'URL')
        self.ytsm._add_channel('2', 'aTest', 'URL')
        self.ytsm._add_channel('3', 'tEStA', 'URL')
        self.ytsm._add_channel('4', 'atEsTa', 'URL')
        self.ytsm._add_channel('5', 'not', 'URL')

        self.assertEqual([
            Channel('1', 'TEST', 'URL'),
            Channel('2', 'aTest', 'URL'),
            Channel('3', 'tEStA', 'URL'),
            Channel('4', 'atEsTa', 'URL')], self.ytsm.find_channels('test'))

    def test_get_all_channels(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_channel('test2', 'Name', 'URL')
        self.ytsm._add_channel('test3', 'Name', 'URL')

        self.assertEqual([
            Channel('test', 'Name', 'URL'),
            Channel('test2', 'Name', 'URL'),
            Channel('test3', 'Name', 'URL')], self.ytsm.get_all_channels())

    def test__add_video(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.assertEqual(Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
                         self.ytsm.get_video('test'))

    def test__add_video_raises_ChannelDoesNotExist(self):
        self.assertRaises(YTSubManager.ChannelDoesNotExist, self.ytsm._add_video, 'test', 'test', 'Name', 'Url',
                          '22-02-01', 'Desc', 'Thumbnail')

    def test__add_video_raises_VideoAlreadyExists(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.assertRaises(YTSubManager.VideoAlreadyExists, self.ytsm._add_video, 'test', 'test', 'Name', 'Url',
                          '22-02-01', 'Desc', 'Thumbnail')

    def test_get_video(self):
        self.ytsm._add_channel('test', 'Test Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.assertEqual(Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
                         self.ytsm.get_video('test'))

    def test_get_video_raises_VideoDoesNotExist(self):
        self.assertRaises(YTSubManager.VideoDoesNotExist, self.ytsm.get_video, 'test')

    def test_find_video_by_name(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_channel('test2', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'aNaMe', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test3', 'test', 'nAMEa', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test4', 'test2', 'aNaMea', 'Url', '22-02-01', 'Desc', 'Thumbnail')

        # All
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'aNaMe', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test3', 'test', 'nAMEa', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test4', 'test2', 'aNaMea', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False)
        ], self.ytsm.find_video_by_name('name'))

        # Only channel with id: "test"
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'aNaMe', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test3', 'test', 'nAMEa', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
        ], self.ytsm.find_video_by_name('NAME', channel_id='test'))

        # Only channel with id: "test2"
        self.assertEqual([
            Video('test4', 'test2', 'aNaMea', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False)
        ], self.ytsm.find_video_by_name('name', channel_id='test2'))

        # No matches
        self.assertEqual([], self.ytsm.find_video_by_name('666'))
        self.assertEqual([], self.ytsm.find_video_by_name('666', channel_id='test'))

    def test_find_video_by_desc(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_channel('test2', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'adEsc', 'Thumbnail')
        self.ytsm._add_video('test3', 'test', 'Name', 'Url', '22-02-01', 'DeSCa', 'Thumbnail')
        self.ytsm._add_video('test4', 'test2', 'Name', 'Url', '22-02-01', 'aDESCa', 'Thumbnail')

        # All
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'Name', 'Url', '22-02-01', 'adEsc', 'Thumbnail', True, False),
            Video('test3', 'test', 'Name', 'Url', '22-02-01', 'DeSCa', 'Thumbnail', True, False),
            Video('test4', 'test2', 'Name', 'Url', '22-02-01', 'aDESCa', 'Thumbnail', True, False)
        ], self.ytsm.find_video_by_desc('desc'))

        # Only channel with id: "test"
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'Name', 'Url', '22-02-01', 'adEsc', 'Thumbnail', True, False),
            Video('test3', 'test', 'Name', 'Url', '22-02-01', 'DeSCa', 'Thumbnail', True, False),
        ], self.ytsm.find_video_by_desc('DESC', channel_id='test'))

        # Only channel with id: "test2"
        self.assertEqual([
            Video('test4', 'test2', 'Name', 'Url', '22-02-01', 'aDESCa', 'Thumbnail', True, False)
        ], self.ytsm.find_video_by_desc('deSc', channel_id='test2'))

        # No matches
        self.assertEqual([], self.ytsm.find_video_by_desc('666'))
        self.assertEqual([], self.ytsm.find_video_by_desc('666', channel_id='test'))

    def test_get_all_videos(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_channel('test2', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')

        # All
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False)
        ], self.ytsm.get_all_videos())

        # Only channel with id: "test"
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
        ], self.ytsm.get_all_videos(channel_id='test'))

        # Only channel with id: "test2"
        self.assertEqual([
            Video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False)
        ], self.ytsm.get_all_videos(channel_id='test2'))

        # No matches
        self.assertEqual([], self.ytsm.get_all_videos(channel_id='666'))

    def test_mark_video_as_old(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm.mark_video_as_old('test')
        self.assertEqual(False, self.ytsm.get_video('test').new)
        self.assertEqual(True, self.ytsm.get_video('test2').new)

    def test_mark_all_videos_old(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_video('test1', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm.mark_all_videos_old('test')
        self.assertEqual(False, self.ytsm.get_video('test1').new)
        self.assertEqual(False, self.ytsm.get_video('test2').new)

    def test_mark_video_as_watched(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm.mark_video_as_watched('test')
        self.assertEqual(True, self.ytsm.get_video('test').watched)
        self.assertEqual(False, self.ytsm.get_video('test2').watched)

    def test_mark_all_videos_watched(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_video('test1', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm.mark_all_videos_watched('test')
        self.assertEqual(True, self.ytsm.get_video('test1').watched)
        self.assertEqual(True, self.ytsm.get_video('test2').watched)

    def test_get_all_new_videos(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_channel('test2', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')

        # Set as OLD to check they do not exist
        self.ytsm._add_video('test5', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm.mark_video_as_old('test5')
        self.ytsm._add_video('test6', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm.mark_video_as_old('test6')

        # All
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False)
        ], self.ytsm.get_all_new_videos())

        # Only channel with id: "test"
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
        ], self.ytsm.get_all_new_videos(channel_id='test'))

        # Only channel with id: "test2"
        self.assertEqual([
            Video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False)
        ], self.ytsm.get_all_new_videos(channel_id='test2'))

        # No matches
        self.assertEqual([], self.ytsm.get_all_new_videos(channel_id='666'))

    def test_get_all_unwatched_videos(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_channel('test2', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')

        # Set as OLD to check they do not exist
        self.ytsm._add_video('test5', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm.mark_video_as_watched('test5')
        self.ytsm._add_video('test6', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm.mark_video_as_watched('test6')

        # All
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False)
        ], self.ytsm.get_all_unwatched_videos())

        # Only channel with id: "test"
        self.assertEqual([
            Video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
            Video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False),
        ], self.ytsm.get_all_unwatched_videos(channel_id='test'))

        # Only channel with id: "test2"
        self.assertEqual([
            Video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail', True, False)
        ], self.ytsm.get_all_unwatched_videos(channel_id='test2'))

        # No matches
        self.assertEqual([], self.ytsm.get_all_unwatched_videos(channel_id='666'))

    def test_get_all_videos_by_date_range(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_channel('test2', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test3', 'test', 'Name', 'Url', '22-02-03', 'Desc', 'Thumbnail')

        self.ytsm._add_video('test4', 'test2', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test5', 'test2', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test6', 'test2', 'Name', 'Url', '22-02-03', 'Desc', 'Thumbnail')

        # All
        self.assertEqual([
            Video('test2', 'test', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail', True, False),
            Video('test5', 'test2', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail', True, False),

        ], self.ytsm.get_all_videos_by_date_range('22-02-01', '22-02-03'))

        # Only channel with id: "test"
        self.assertEqual([
            Video('test2', 'test', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail', True, False),
        ], self.ytsm.get_all_videos_by_date_range('22-02-01', '22-02-03', channel_id='test'))

        # Only channel with id: "test2"
        self.assertEqual([
            Video('test5', 'test2', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail', True, False),
        ], self.ytsm.get_all_videos_by_date_range('22-02-01', '22-02-03', channel_id='test2'))

        # No matches
        self.assertEqual([], self.ytsm.get_all_videos_by_date_range('22-02-03', '22-02-05'))
        self.assertEqual([], self.ytsm.get_all_videos_by_date_range('22-02-01', '22-02-03', channel_id='666'))

    def test_get_amt_videos(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_channel('test2', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail')
        self.ytsm._add_video('test3', 'test', 'Name', 'Url', '22-02-03', 'Desc', 'Thumbnail')
        self.ytsm.mark_video_as_old('test3')
        self.ytsm.mark_video_as_old('test2')
        self.ytsm.mark_video_as_watched('test3')
        self.assertEqual((3, 1, 2), self.ytsm.get_amt_videos(channel_id='test'))
        self.assertEqual((0, 0, 0), self.ytsm.get_amt_videos(channel_id='666'))

    def test__remove_video(self):
        self.ytsm._add_channel('test', 'Name', 'URL')
        self.ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self.ytsm._remove_video('test')
        self.assertRaises(self.ytsm.VideoDoesNotExist, self.ytsm.get_video, 'test')
