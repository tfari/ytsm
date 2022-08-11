""" Tests for YTScraper, uses files at /files_for_tests. """
import json
import os.path
from unittest import TestCase
from ytsm.scraper.yt_scraper import YTScraper
from ytsm.scraper.helpers.req_handler import InvalidStatusCode, ReqHandlerError

FILE_PATH = os.path.dirname(os.path.abspath(__file__)) + '/files_for_tests'
XML_EXAMPLE_CNN = FILE_PATH + '/example_xml_cnn.xml'
JSON_EXAMPLE_VIDEOS_CNN = FILE_PATH + '/json_example_videos_cnn.json'

class TestYTScraper(TestCase):
    @staticmethod
    def _raiser_helper(ex):
        """ Monkey patch raises """
        raise ex

    def setUp(self) -> None:
        """ Create a new YTScraper for each test """
        self.ytscraper = YTScraper()

    def test__fix_schema(self):
        test_url = 'https://abc.com'
        self.assertEqual(test_url, self.ytscraper._fix_schema('abc.com'))
        self.assertEqual(test_url, self.ytscraper._fix_schema('http://abc.com'))
        self.assertEqual(test_url, self.ytscraper._fix_schema('https://abc.com'))
        # Special case
        self.assertEqual("https://abchttp.com", self.ytscraper._fix_schema("abchttp.com"))
        self.assertEqual("https://abchttp.com", self.ytscraper._fix_schema("http://abchttp.com"))

    def test__validate_url(self):
        self.ytscraper._validate_url('youtube.com/watch?v=test')
        self.ytscraper._validate_url('youtube.com/channel/test')
        self.ytscraper._validate_url('youtube.com/user/test')
        self.ytscraper._validate_url('youtube.com/c/test')

    def test__validate_url_raises_UrlNotYT(self):
        self.assertRaises(YTScraper.UrlNotYT, self.ytscraper._validate_url, 'test.com/channel/test')

    def test__validate_url_raises_YTUrlNotSupported(self):
        self.assertRaises(YTScraper.YTUrlNotSupported, self.ytscraper._validate_url, 'youtube.com/test')

    def test_clear_cache(self):
        self.ytscraper.cache = {'abc': 0}
        self.ytscraper.clear_cache()
        self.assertEqual({}, self.ytscraper.cache)

    def test_get_channel_id_and_thumbnail_from_url(self):
        self.ytscraper._get_url = lambda x: 'channelId" content="UCupvZG-5ko_eiXAupbDfxWw"extra_text ' \
                                            '"url":"https://yt3.ggpht.com' \
                                            '/FJzSJC_BbfPzbDW0JUF1Jbc5Q3bELn4ntoAmzS0sNlxQEuEXnMwkhI1r1dKpRbnicd60tdwy'\
                                            'rlc=s88-c-k-c0x00ffffff-no-rj"afafaf" '

        expected = ('UCupvZG-5ko_eiXAupbDfxWw',
                    'https://yt3.ggpht.com/FJzSJC_BbfPzbDW0JUF1Jbc5Q3bELn4ntoAmzS0sNlxQEuEXnMwkhI1r1dKpRbnicd60tdwyrlc')
        self.assertEqual(expected, self.ytscraper.get_channel_id_and_thumbnail_from_url(
            'https://youtube.com/channel/test'))

    def test_get_channel_id_and_thumbnail_from_url_lets_raises_escalate(self):
        self.assertRaises(YTScraper.UrlNotYT, self.ytscraper.get_channel_id_and_thumbnail_from_url, 'test.com')

        self.assertRaises(YTScraper.YTUrlNotSupported, self.ytscraper.get_channel_id_and_thumbnail_from_url, 'youtube.com/test')

        valid_yt_url_for_m_patched_raises = 'youtube.com/channel/test'
        self.ytscraper._get_url = lambda x: self._raiser_helper(YTScraper.YTUrl404('666'))
        self.assertRaises(YTScraper.YTUrl404, self.ytscraper.get_channel_id_and_thumbnail_from_url, valid_yt_url_for_m_patched_raises)

        self.ytscraper._get_url = lambda x: self._raiser_helper(YTScraper.YTUrlUnexpectedStatusCode('666'))
        self.assertRaises(YTScraper.YTUrlUnexpectedStatusCode,
                          self.ytscraper.get_channel_id_and_thumbnail_from_url, valid_yt_url_for_m_patched_raises)

        self.ytscraper._get_url = lambda x: self._raiser_helper(YTScraper.GettingError('666'))
        self.assertRaises(YTScraper.GettingError,
                          self.ytscraper.get_channel_id_and_thumbnail_from_url, valid_yt_url_for_m_patched_raises)

        self.ytscraper._get_url = lambda x: '666'  # No need to monkeypatch _extract_channel_id_from_html, just pass 666
        self.assertRaises(YTScraper.ChannelIDParsingError,
                          self.ytscraper.get_channel_id_and_thumbnail_from_url, valid_yt_url_for_m_patched_raises)

        self.ytscraper._get_url = lambda x: '666'
        self.ytscraper._extract_channel_id_from_html = lambda x, y: '666'
        self.assertRaises(YTScraper.ChannelThumbnailParsingError,
                          self.ytscraper.get_channel_id_and_thumbnail_from_url, valid_yt_url_for_m_patched_raises)

    def test__extract_channel_id_from_html(self):
        # Simple
        self.assertEqual('test', self.ytscraper._extract_channel_id_from_html('channelId" content="test"extra_text',
                                                                              'test'))

    def test__extract_channel_id_from_html_raises_ChannelIDParsingError(self):
        self.assertRaises(YTScraper.ChannelIDParsingError, self.ytscraper._extract_channel_id_from_html, '666', 'test')

    def test__extract_channel_thumbnail_url_from_html(self):
        expected = 'https://yt3.ggpht.com/FJzSJC_BbfPzbDW0JUF1Jbc5Q3bELn4ntoAmzS0sNlxQEuEXnMwkhI1r1dKpRbnicd60tdwyrlc'
        test = '"url":"https://yt3.ggpht.com' \
               '/FJzSJC_BbfPzbDW0JUF1Jbc5Q3bELn4ntoAmzS0sNlxQEuEXnMwkhI1r1dKpRbnicd60tdwyrlc=s88' \
               '-c-k-c0x00ffffff-no-rj"afafaf'
        self.assertEqual(expected, self.ytscraper._extract_channel_thumbnail_url_from_html(test, 'test'))

    def test__extract_channel_thumbnail_url_from_html_raises_ChannelThumbnailParsingError(self):
        self.assertRaises(YTScraper.ChannelThumbnailParsingError,
                          self.ytscraper._extract_channel_thumbnail_url_from_html, '666', 'test')

    def test_get_channel_information(self):
        with open(XML_EXAMPLE_CNN, 'r', encoding='utf-8') as r_file:
            read_xml = r_file.read()
            self.ytscraper._get_url = lambda x: read_xml  # Monkey patch _get_url
            self.assertEqual({'id': 'Test',
                              'name': 'CNN',
                              'url': 'https://www.youtube.com/channel/UCupvZG-5ko_eiXAupbDfxWw'},
                             self.ytscraper.get_channel_information('Test'))
            # Check text cache:
            self.assertEqual({'Test': read_xml}, self.ytscraper.cache)

    def test_get_channel_information_lets_raises_escalate(self):
        self.ytscraper._get_url = lambda x: self._raiser_helper(YTScraper.YTUrl404('666'))
        self.assertRaises(YTScraper.YTUrl404, self.ytscraper.get_channel_information, 'Test')

        self.ytscraper._get_url = lambda x: self._raiser_helper(YTScraper.YTUrlUnexpectedStatusCode('666'))
        self.assertRaises(YTScraper.YTUrlUnexpectedStatusCode, self.ytscraper.get_channel_information, 'Test')

        self.ytscraper._get_url = lambda x: self._raiser_helper(YTScraper.GettingError('666'))
        self.assertRaises(YTScraper.GettingError, self.ytscraper.get_channel_information, 'Test')

        self.ytscraper._get_url = lambda x: '666'  # No need to monkeypatch _extract_channel_id_from_html, just pass 666
        self.assertRaises(YTScraper.ChannelInfoParsingError, self.ytscraper.get_channel_information, 'Test')

    def test__extract_channel_information(self):
        with open(XML_EXAMPLE_CNN, 'r', encoding='utf-8') as r_file:
            self.assertEqual({'id': 'Test',
                              'name': 'CNN',
                              'url': 'https://www.youtube.com/channel/UCupvZG-5ko_eiXAupbDfxWw'},
                             self.ytscraper._extract_channel_information(r_file.read(), 'Test'))

    def test__extract_channel_information_raises_ChannelInfoParsingError(self):
        self.assertRaises(YTScraper.ChannelInfoParsingError, self.ytscraper._extract_channel_information, '666', 'test')

    def test_get_video_list(self):
        with open(JSON_EXAMPLE_VIDEOS_CNN, 'r', encoding='utf-8') as json_file:
            expected_results = json.loads(json_file.read())
            with open(XML_EXAMPLE_CNN, 'r', encoding='utf-8') as xml_file:
                self.ytscraper._get_url = lambda x: xml_file.read()
                self.assertEqual(expected_results, self.ytscraper.get_video_list('UCupvZG-5ko_eiXAupbDfxWw'))

        # Using cache
        with open(JSON_EXAMPLE_VIDEOS_CNN, 'r', encoding='utf-8') as json_file:
            expected_results = json.loads(json_file.read())
            with open(XML_EXAMPLE_CNN, 'r', encoding='utf-8') as xml_file:
                self.ytscraper.cache['UCupvZG-5ko_eiXAupbDfxWw'] = xml_file.read()
                self.assertEqual(expected_results, self.ytscraper.get_video_list('UCupvZG-5ko_eiXAupbDfxWw',
                                                                                 use_cache=True))

    def test_get_video_list_raises_CacheDoesNotHaveKey(self):
        self.assertRaises(YTScraper.CacheDoesNotHaveKey, self.ytscraper.get_video_list, '666', use_cache=True)

    def test_get_video_list_lets_raises_escalate(self):
        self.ytscraper._get_url = lambda x: self._raiser_helper(YTScraper.YTUrl404('666'))
        self.assertRaises(YTScraper.YTUrl404, self.ytscraper.get_video_list, 'Test')

        self.ytscraper._get_url = lambda x: self._raiser_helper(YTScraper.YTUrlUnexpectedStatusCode('666'))
        self.assertRaises(YTScraper.YTUrlUnexpectedStatusCode, self.ytscraper.get_video_list, 'Test')

        self.ytscraper._get_url = lambda x: self._raiser_helper(YTScraper.GettingError('666'))
        self.assertRaises(YTScraper.GettingError, self.ytscraper.get_video_list, 'Test')

        self.ytscraper._get_url = lambda x: '<entry></entry>'
        self.assertRaises(YTScraper.VideoListParsingError, self.ytscraper.get_video_list, 'Test')

    def test_get_video_list_multiple(self):
        """ Tightly paired with _get_urls_parallel """
        # 1 - Check the url_list is done right
        expected = [self.ytscraper._rss_base_url % 'test_1', self.ytscraper._rss_base_url % 'test_2']

        class MonkeyPatchedResponse:
            """ MP """
            def __init__(self):
                self.urls: list[str] = []

            def make_bulk_queries(self, url_list: list[str]):
                """ MP method """
                self.urls = url_list
                return [], []
        MPR = MonkeyPatchedResponse()
        self.ytscraper.scrap_wrapper.make_bulk_queries = MPR.make_bulk_queries
        self.ytscraper.get_video_list_multiple(['test_1', 'test_2'])
        self.assertEqual(expected, MPR.urls)

        # 2 - Check it creates return dictionary right
        self.ytscraper._get_urls_parallel = lambda x: {'aaa': 1, 'bbb': 2}
        self.ytscraper._extract_video_information_from_xml = lambda x, y: 777
        expected = {'aaa': 777, 'bbb': 777}
        self.assertEqual(expected, self.ytscraper.get_video_list_multiple(['test']))

    def test_get_video_list_multiple_lets_raises_escalate(self):
        self.ytscraper._get_urls_parallel = lambda x: self._raiser_helper(YTScraper.YTUrl404(''))
        self.assertRaises(YTScraper.YTUrl404, self.ytscraper.get_video_list_multiple, ['666'])

        self.ytscraper._get_urls_parallel = lambda x: self._raiser_helper(YTScraper.YTUrlUnexpectedStatusCode(''))
        self.assertRaises(YTScraper.YTUrlUnexpectedStatusCode, self.ytscraper.get_video_list_multiple, ['666'])

        self.ytscraper._get_urls_parallel = lambda x: self._raiser_helper(YTScraper.GettingError(''))
        self.assertRaises(YTScraper.GettingError, self.ytscraper.get_video_list_multiple, ['666'])

        self.ytscraper._get_urls_parallel = lambda x: {'a': 666}
        self.ytscraper._extract_video_information_from_xml = \
            lambda x, y: self._raiser_helper(YTScraper.VideoListParsingError(''))
        self.assertRaises(YTScraper.VideoListParsingError, self.ytscraper.get_video_list_multiple, ['666'])

    def test__extract_video_information_from_xml(self):
        with open(JSON_EXAMPLE_VIDEOS_CNN, 'r', encoding='utf-8') as json_file:
            expected_results = json.loads(json_file.read())
            with open(XML_EXAMPLE_CNN, 'r', encoding='utf-8') as xml_file:
                self.assertEqual(expected_results, self.ytscraper._extract_video_information_from_xml(
                    xml_file.read(), 'UCupvZG-5ko_eiXAupbDfxWw'))

    def test__extract_video_information_from_xml_raises_VideoListParsingError(self):
        broken_xml = '<entry></entry>'
        self.assertRaises(YTScraper.VideoListParsingError, self.ytscraper._extract_video_information_from_xml,
                          broken_xml, 'Test')

    def test__get_url(self):
        # Monkey patch self.scrap_wrapper.make_unique_query to make sure method return's response.text
        class MonkeyPatchedResponse:
            """ MP """
            def __init__(self):
                self.text = 'Test'

        self.ytscraper.scrap_wrapper.make_unique_query = lambda x: MonkeyPatchedResponse()
        self.assertEqual('Test', self.ytscraper._get_url('TestUrl'))

    def test__get_url_raises_YTUrl404_on_InvalidStatusCode404(self):
        self.ytscraper.scrap_wrapper.make_unique_query = lambda x: self._raiser_helper(InvalidStatusCode('Test', 404))
        self.assertRaises(YTScraper.YTUrl404, self.ytscraper._get_url, '666')

    def test__get_url_raises_YTUrlUnexpectedStatusCode_on_InvalidStatusCode_NOT_404(self):
        self.ytscraper.scrap_wrapper.make_unique_query = lambda x: self._raiser_helper(InvalidStatusCode('Test', 666))
        self.assertRaises(YTScraper.YTUrlUnexpectedStatusCode, self.ytscraper._get_url, '666')

    def test__get_url_raises_GettingError_on_ReqHandlerError(self):
        self.ytscraper.scrap_wrapper.make_unique_query = lambda x: self._raiser_helper(ReqHandlerError(666))
        self.assertRaises(YTScraper.GettingError, self.ytscraper._get_url, '666')

    def test__get_urls_parallel(self):
        class MonkeyPatchedResponse:
            """ MP """
            def __init__(self, url: str):
                self.url = f'channel_id={url}'
                self.text = 'test'
        self.ytscraper.scrap_wrapper.make_bulk_queries = lambda x: [[MonkeyPatchedResponse('1'),
                                                                    MonkeyPatchedResponse('2'),
                                                                    MonkeyPatchedResponse('3')], []]
        expected = {'1': 'test', '2': 'test', '3': 'test'}
        self.assertEqual(expected, self.ytscraper._get_urls_parallel(['test']))

    def test__get_urls_parallel_raises_YTUrl404_on_InvalidStatusCode404(self):
        class MonkeyPatchedStatusCode:
            """ MP """
            def __init__(self):
                self.status_code = 404
        self.ytscraper.scrap_wrapper.make_bulk_queries = lambda x: [[], [{'error': InvalidStatusCode,
                                                                          'response': MonkeyPatchedStatusCode(),
                                                                          'url': '666'}]]
        self.assertRaises(YTScraper.YTUrl404, self.ytscraper._get_urls_parallel, [666])

    def test__get_urls_parallel_raises_YTUrlUnexpectedStatusCode_on_InvalidStatusCode_NOT_404(self):
        class MonkeyPatchedStatusCode:
            """ MP """
            def __init__(self):
                self.status_code = 666
        self.ytscraper.scrap_wrapper.make_bulk_queries = lambda x: [[], [{'error': InvalidStatusCode,
                                                                          'response': MonkeyPatchedStatusCode()}]]
        self.assertRaises(YTScraper.YTUrlUnexpectedStatusCode, self.ytscraper._get_urls_parallel, [666])

    def test__get_urls_parallel_raises_GettingError_on_ReqHandlerError(self):
        self.ytscraper.scrap_wrapper.make_bulk_queries = lambda x: [[], [{'error': ReqHandlerError}]]
        self.assertRaises(YTScraper.GettingError, self.ytscraper._get_urls_parallel, [666])
