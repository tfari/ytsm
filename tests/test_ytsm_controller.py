""" Tests for YTSMController """

from unittest import TestCase, mock
from ytsm.ytsubmanager import YTSubManager
from ytsm.repository.sqlite_repository import SQLiteRepository
from ytsm.uis.ytsm_controller import YTSMController

from ytsm.settings import SQLITE_DB_CREATION_STATEMENTS

class TestYTSMController(TestCase):
    def setUp(self) -> None:
        """ Set up the DB, YTSM  and YTSCM instances """
        repo = SQLiteRepository(db_path=':memory:')
        for sqlite_statement in SQLITE_DB_CREATION_STATEMENTS:
            repo.cur.execute(sqlite_statement)

        self._ytsm = YTSubManager(repository=repo)

        self.ytsmc = YTSMController(self._ytsm)

    def test_make_channel_dto(self):
        self._ytsm._add_channel('test', 'Test', 'abcd', 'thumbnail')
        c = self._ytsm.get_channel('test')
        self._ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self._ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self._ytsm._add_video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self._ytsm.mark_video_as_old('test')
        self._ytsm.mark_video_as_old('test2')
        self._ytsm.mark_video_as_watched('test')

        expected_cdto = YTSMController.ChannelDTO(channel=c, new=1, unwatched=2, total=3)
        self.assertEqual(expected_cdto, self.ytsmc.make_channel_dto(c))

    def test_make_video_dto(self):
        self._ytsm._add_channel('test', 'Test', 'abcd', 'thumbnail')
        self._ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        video = self._ytsm.get_video('test')
        expected_vdto = YTSMController.VideoDTO(video=video, channel_name='Test')
        self.assertEqual(expected_vdto, self.ytsmc.make_video_dto(video))

    def test_get_channel_dto_list(self):
        self._ytsm._add_channel('test', 'bTest', 'abcd', 'thumbnail')  # Check sorting (bTest / aTest)
        self._ytsm._add_channel('test2', 'aTest', 'abcd', 'thumbnail')

        c = self._ytsm.get_channel('test')
        c1 = self._ytsm.get_channel('test2')
        expected = [YTSMController.ChannelDTO(c1, 0, 0, 0), YTSMController.ChannelDTO(c, 0, 0, 0)]
        self.assertEqual(expected, self.ytsmc.get_channel_dto_list())

    def test_set_channel_search_term(self):
        self._ytsm._add_channel('test', 'Test', 'abcd', 'thumbnail')
        self._ytsm._add_channel('test2', '666', 'abcd', 'thumbnail')
        c1 = self._ytsm.get_channel('test2')
        expected = [YTSMController.ChannelDTO(c1, 0, 0, 0)]
        self.ytsmc.set_channel_search_term('666')
        self.assertEqual(expected, self.ytsmc.get_channel_dto_list())

    def test_get_video_dto_list(self):
        # Set up
        self._ytsm._add_channel('test', 'Test', 'abcd', 'thumbnail')
        self._ytsm._add_channel('test2', 'Test2', 'abcd', 'thumbnail')
        self._ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-04', 'Desc', 'Thumbnail')
        self._ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-03', 'Desc', 'Thumbnail')
        self._ytsm._add_video('test3', 'test2', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail')
        v1 = self._ytsm.get_video('test')
        v2 = self._ytsm.get_video('test2')
        v3 = self._ytsm.get_video('test3')

        # Channel id
        self.assertEqual([YTSMController.VideoDTO(v1, 'Test'), YTSMController.VideoDTO(v2, 'Test')],
                         self.ytsmc.get_video_dto_list('test'))
        self.assertEqual([YTSMController.VideoDTO(v3, 'Test2')], self.ytsmc.get_video_dto_list('test2'))

        # self.ytsmc.get_video_dto_list counts as visiting a channel, meaning they are no longer new!
        v1.new, v2.new, v3.new = False, False, False

        # All videos
        self.assertEqual([YTSMController.VideoDTO(v1, 'Test'),
                          YTSMController.VideoDTO(v2, 'Test'),
                         YTSMController.VideoDTO(v3, 'Test2')],
                         self.ytsmc.get_video_dto_list('test', all_videos=True))

    def test_set_video_filter(self):
        # Set up
        self._ytsm._add_channel('test', 'Test', 'abcd', 'thumbnail')
        self._ytsm._add_channel('test2', 'Test2', 'abcd', 'thumbnail')
        self._ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-04', 'Desc', 'Thumbnail')
        self._ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-03', 'Desc', 'Thumbnail')
        self._ytsm._add_video('test3', 'test2', 'Name', 'Url', '22-02-02', 'Desc', 'Thumbnail')
        v1 = self._ytsm.get_video('test')
        v2 = self._ytsm.get_video('test2')
        v3 = self._ytsm.get_video('test3')

        self.ytsmc.mark_video_watched(YTSMController.VideoDTO(v1, '666'))
        self._ytsm.mark_video_as_old('test2')

        # self.ytsmc.get_video_dto_list counts as visiting a channel, meaning they are no longer new!
        v1.new, v2.new, v1.watched = False, False, True

        # 1 - NEW
        self.ytsmc.set_video_filter(YTSMController.NEW)
        self.assertEqual([YTSMController.VideoDTO(v3, 'Test2')],
                         self.ytsmc.get_video_dto_list(channel_id='999', all_videos=True)
                         )

        # 2 - UNWATCHED
        self.ytsmc.set_video_filter(YTSMController.UNWATCHED)
        self.assertEqual([YTSMController.VideoDTO(v2, 'Test'),
                          YTSMController.VideoDTO(v3, 'Test2')
                          ],
                         self.ytsmc.get_video_dto_list(channel_id='999', all_videos=True))

        # 3 - ALL
        self.ytsmc.set_video_filter(YTSMController.ALL)
        self.assertEqual([YTSMController.VideoDTO(v1, 'Test'),
                          YTSMController.VideoDTO(v2, 'Test'),
                          YTSMController.VideoDTO(v3, 'Test2')
                          ],
                         self.ytsmc.get_video_dto_list(channel_id='999', all_videos=True))

    def test_set_video_filter_raises_ValueError(self):
        self.assertRaises(ValueError, self.ytsmc.set_video_filter, '666')

    def test_set_video_search_type_and_term(self):
        # Set up
        self._ytsm._add_channel('test', 'Test', 'abcd', 'thumbnail')
        self._ytsm._add_channel('test2', 'Test2', 'abcd', 'thumbnail')
        self._ytsm._add_video('test', 'test', '666', 'Url', '2022-02-01', 'Desc', 'Thumbnail')
        self._ytsm._add_video('test2', 'test', 'Name', 'Url', '2022-02-03', '666', 'Thumbnail')
        self._ytsm._add_video('test3', 'test2', '666', 'Url', '2022-02-04', 'Desc', 'Thumbnail')
        v1 = self._ytsm.get_video('test')
        v2 = self._ytsm.get_video('test2')
        v3 = self._ytsm.get_video('test3')
        self.ytsmc.set_video_search_term('666')
        self.ytsmc.set_video_search_type(YTSMController.NAME)

        # NAME + channel_id
        self.assertEqual([YTSMController.VideoDTO(v3, 'Test2')], self.ytsmc.get_video_dto_list('test2'))
        # self.ytsmc.get_video_dto_list counts as visiting a channel, meaning they are no longer new!
        v3.new = False

        # NAME + all
        self.assertEqual([YTSMController.VideoDTO(v3, 'Test2'), YTSMController.VideoDTO(v1, 'Test')],
                         self.ytsmc.get_video_dto_list(channel_id='777', all_videos=True))
        v1.new = False

        self.ytsmc.set_video_search_type(YTSMController.DESC)
        # DESC + channel_id
        self.assertEqual([], self.ytsmc.get_video_dto_list('test2'))
        # DESC + all
        self.assertEqual([YTSMController.VideoDTO(v2, 'Test')], self.ytsmc.get_video_dto_list('test', all_videos=True))
        v2.new = False

        # DATE + channel_id
        self.ytsmc.set_video_search_type(YTSMController.DATE)
        # # WRONG
        self.ytsmc.set_video_search_term('abcd')
        self.assertEqual([], self.ytsmc.get_video_dto_list('test', all_videos=True))

        # # GOOD
        self.ytsmc.set_video_search_term('2022-07-08 2022-08-09')

        self.assertEqual([], self.ytsmc.get_video_dto_list('test'))
        self.assertEqual([], self.ytsmc.get_video_dto_list('test', all_videos=True))

        self.ytsmc.set_video_search_term('2022-01-31 2022-02-31')
        self.assertEqual([YTSMController.VideoDTO(v2, 'Test'), YTSMController.VideoDTO(v1, 'Test')],
                         self.ytsmc.get_video_dto_list(channel_id='test'))

        # DATE + all
        self.assertEqual([YTSMController.VideoDTO(v3, 'Test2'), YTSMController.VideoDTO(v2, 'Test'),
                          YTSMController.VideoDTO(v1, 'Test')],
                         self.ytsmc.get_video_dto_list(channel_id='999', all_videos=True))

    def test_set_video_search_type_raises_ValueError(self):
        self.assertRaises(ValueError, self.ytsmc.set_video_search_type, '666')

    def test_add_channel(self):
        # Assert it calls ytsm.add_channel, and returns the channel with the id that ytsm returns
        self._ytsm._add_channel('666', 'Test', 'ads', 'thumbnail')
        c = self._ytsm.get_channel('666')
        self._ytsm.add_channel = lambda x: '666'
        self.assertEqual(c, self.ytsmc.add_channel('test'))

    def test_add_channel_raises_AddChannelError(self):
        def raiser(x):
            """ Monkeypatch a raise """
            raise YTSubManager.BaseYTSMError(x)

        self._ytsm.add_channel = raiser
        self.assertRaises(YTSMController.AddChannelError, self.ytsmc.add_channel, '666')

    def test_remove_channel(self):
        self._ytsm._add_channel('test', 'Test', 'abc', 'thumbnail')
        c = self._ytsm.get_channel('test')
        self.ytsmc.remove_channel(YTSMController.ChannelDTO(c, 0, 0, 0))
        self.assertEqual([], self.ytsmc.get_channel_dto_list())
        self.assertEqual([], self._ytsm.get_all_channels())

    def test_mark_channel_all_watched(self):
        self._ytsm._add_channel('test', 'Test', 'abc', 'thumbnail')
        self._ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self._ytsm._add_video('test2', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        self._ytsm._add_video('test3', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')

        # OTHERS
        self._ytsm._add_channel('666', 'Test', 'abc', 'thumbnail')
        self._ytsm._add_video('test4', '666', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')

        c = self._ytsm.get_channel('test')
        self.ytsmc.mark_channel_all_watched(YTSMController.ChannelDTO(c, 0, 0, 0))

        self.assertEqual([], self._ytsm.get_all_unwatched_videos(channel_id='test'))

    def test_update_channel(self):
        self._ytsm._add_channel('test', 'Test', 'abc', 'thumbnail')
        c = self._ytsm.get_channel('test')
        self._ytsm.update_channel = lambda x: x.upper()  # This way we also test the channel_id was passed
        self.assertEqual('TEST', self.ytsmc.update_channel(YTSMController.ChannelDTO(c, 0, 0, 0)))

    def test_update_channel_raises_UpdateChannelError(self):
        self._ytsm._add_channel('test', 'Test', 'abc', 'thumbnail')
        c = self._ytsm.get_channel('test')

        def raiser(x):
            """ Monkeypatch a raise """
            raise YTSubManager.BaseYTSMError(x)

        self._ytsm.update_channel = raiser
        cdto = YTSMController.ChannelDTO(c, 0, 0, 0)
        self.assertRaises(YTSMController.UpdateChannelError, self.ytsmc.update_channel, cdto)

    def test_update_all_channels(self):
        self._ytsm._add_channel('test', 'Test', 'abc', 'thumbnail')
        self._ytsm._add_channel('test2', 'Test', 'abc', 'thumbnail')
        self._ytsm._add_channel('test3', 'Test', 'abc', 'thumbnail')
        self._ytsm.update_all_channels = lambda: {'total': 666, 'new': {'test': 1, 'test2': 2, 'test3': 8},
                                                  'errs': {'test4': 11, 'test5': 12, 'test6': 13}}
        expected = {'total': 666, 'details': [('Test', 1), ('Test', 2), ('Test', 8)],
                    'errs': {'test4': 11, 'test5': 12, 'test6': 13}}
        self.assertEqual(expected, self.ytsmc.update_all_channels())

    def test_update_all_channels_raises_UpdateAllChannelsError(self):
        def raiser():
            """ Monkeypatch a raise """
            raise YTSubManager.BaseYTSMError()
        self._ytsm.update_all_channels = raiser
        self.assertRaises(YTSMController.UpdateAllChannelsError, self.ytsmc.update_all_channels)

    def test_mark_video_watched(self):
        self._ytsm._add_channel('test', 'Test', 'abc', 'thumbnail')
        self._ytsm._add_video('test', 'test', 'Name', 'Url', '22-02-01', 'Desc', 'Thumbnail')
        v = self._ytsm.get_video('test')
        self.ytsmc.mark_video_watched(YTSMController.VideoDTO(v, 'Test'))
        v = self._ytsm.get_video('test')
        self.assertEqual(False, v.new)
        self.assertEqual(True, v.watched)

    @mock.patch("webbrowser.open")
    def test_watch_video(self, mocked_fun):
        self._ytsm._add_channel('test', 'Test', 'abc', 'thumbnail')
        self._ytsm._add_video('test', 'test', 'Name', '666', '22-02-01', 'Desc', 'Thumbnail')
        v = self._ytsm.get_video('test')
        self.ytsmc.watch_video(YTSMController.VideoDTO(v, 'Test'))
        v = self._ytsm.get_video('test')

        mocked_fun.assert_called_with('666')
        self.assertEqual(False, v.new)
        self.assertEqual(True, v.watched)

    @mock.patch("webbrowser.open")
    def test_visit_channel(self, mocked_fun):
        self._ytsm._add_channel('test', 'Test', '666', 'abc')
        c = self._ytsm.get_channel('test')
        self.ytsmc.visit_channel(YTSMController.ChannelDTO(c, 0, 0, 0))
        mocked_fun.assert_called_with('666')

    def test_toggle_mute_channel(self):
        self._ytsm._add_channel('test', 'Test', 'abc', 'thumbnail')
        self.ytsmc.toggle_mute_channel(YTSMController.ChannelDTO(self._ytsm.get_channel('test'), 0, 0, 0))
        self.assertEqual(False, self._ytsm.get_channel('test').notify_on)
        self.ytsmc.toggle_mute_channel(YTSMController.ChannelDTO(self._ytsm.get_channel('test'), 0, 0, 0))
        self.assertEqual(True, self._ytsm.get_channel('test').notify_on)
        self.ytsmc.toggle_mute_channel(YTSMController.ChannelDTO(self._ytsm.get_channel('test'), 0, 0, 0))
        self.assertEqual(False, self._ytsm.get_channel('test').notify_on)

    def test_get_channel_dto_from_id(self):
        self._ytsm._add_channel('test', 'Test', 'abc', 'thumbnail')
        c = self._ytsm.get_channel('test')
        self.assertEqual(YTSMController.ChannelDTO(c, 0, 0, 0), self.ytsmc.get_channel_dto_from_id('test'))

    def test_get_channel_dto_from_id_raises_ChannelIDNotFound(self):
        self.assertRaises(YTSMController.ChannelIDNotFound, self.ytsmc.get_channel_dto_from_id, '666')