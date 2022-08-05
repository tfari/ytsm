""" Scrapping class and exceptions. """
import re

from bs4 import BeautifulSoup  # type: ignore

from ytsm.scraper.helpers.scrap_wrappers import ScrapWrapper
from ytsm.scraper.helpers.req_handler import InvalidStatusCode, ReqHandlerError


class YTScraper:
    """
    Class to encapsulate all scraping-related methods

    Has basically three responsibilities:
        * Getting and parsing a channel_id from an YT url
        * Getting and parsing channel_information from a channel_id.
        * Getting and parsing a list of video_information from a channel_id.
    """
    _rss_base_url = 'https://www.youtube.com/feeds/videos.xml?channel_id=%s'
    _supported_url_types = ['youtube.com/watch?v=', 'youtube.com/channel', 'youtube.com/user/', 'youtube.com/c/']
    _channel_id_re = re.compile(r'channelId" content="(?P<channel_id>[\w\-]+)"')
    _channel_thumbnail_re = re.compile(r'"url":"https://yt3(?P<channel_thumbnail>[\w\-./_:]+)=')

    def __init__(self):
        self.scrap_wrapper = ScrapWrapper(headers=None)
        self.cache = {}  # We use this to not waste the xml when getting Channel information

    @staticmethod
    def _fix_schema(input_url) -> str:
        """ Force input_url to use https """
        if not input_url.startswith('https://'):
            force_https = input_url.replace('http', 'https')
            fixed_schema = f'https://{force_https}' if 'http' not in force_https else force_https
            return fixed_schema
        return input_url

    def _validate_url(self, input_url: str) -> None:
        """
        Validate a YT Url
        :raise UrlNotYT: If the url is not a YT url.
        :raise YTUrlNotSupported: If the url is a YT url but is not supported
        """
        if 'youtube.com' not in input_url:
            raise self.UrlNotYT(input_url)

        if not any(url_type in input_url for url_type in self._supported_url_types):
            raise self.YTUrlNotSupported(input_url)

    def clear_cache(self) -> None:
        """ Clears the cache """
        self.cache = {}

    def get_channel_id_and_thumbnail_from_url(self, input_url: str) -> tuple[str, str]:
        """
        Gets a Channel's id and thumbnail from an url.

        :raise UrLNotYT: If the url is not a YT url.
        :raise YTUrlNotSupported: If the url is a YT url but is not supported
        :raise YTUrl404: If the GET request to the url failed with 404.
        :raise YTUrlUnexpectedStatusCode: If the GET failed with a status code other than 404.
        :raise GettingError: If the GET request itself failed.
        :raise ChannelIDParsingError: If parsing failed.
        watch?v= urls don't return 404 when they don't exist, so if input_url was one of those, it
        could very well mean 404.

        :raise ChannelThumbnailParsingError: If parsing failed.

        :return tuple: (channel_id, channel_thumbnail)
        """
        self._validate_url(input_url)  # Raises URLNotYT, YTURLNotSupported
        fixed_url = self._fix_schema(input_url)
        html = self._get_url(fixed_url)
        return self._extract_channel_id_from_html(html, fixed_url), \
               self._extract_channel_thumbnail_url_from_html(html, fixed_url)

    def _extract_channel_id_from_html(self, html: str, input_url: str) -> str:
        """
        Extract channel_id string from a query's html.
        :raise ChannelIDParsingError: If parsing failed.
        """
        match = re.search(self._channel_id_re, html)
        if match:
            return match.group('channel_id')
        raise self.ChannelIDParsingError(input_url)

    def _extract_channel_thumbnail_url_from_html(self, html: str, input_url: str) -> str:
        """
        Extract channel_thumbnail url from a query's html.
        :raise ChannelThumbnailParsingError: If parsing failed.
        """
        match = re.search(self._channel_thumbnail_re, html)
        if match:
            return f'https://yt3{match.group("channel_thumbnail")}'
        raise self.ChannelThumbnailParsingError(input_url)

    def get_channel_information(self, channel_id: str) -> dict:
        """
        Gets a dictionary with channel information from a Channel's id.

        Saves the get_request to self.cache under channel_id key.

        :raise YTUrl404: if YT returns 404
        :raise YTUrlUnexpectedStatusCode: if YT returns something else than 404
        :raise GettingError : if there is any other request error
        :raise ChannelInfoParsingError: if there is any issue with the parsing

        :return: {{'id': str, 'name': str, 'uri': str}
        """
        xml = self._get_url(self._rss_base_url % channel_id)
        self.cache[channel_id] = xml
        return self._extract_channel_information(xml, channel_id)

    def _extract_channel_information(self, xml: str, channel_id: str) -> dict:
        """
        Extract channel's name and uri from a https://www.youtube.com/feeds/videos.xml?channel_id=
        query's xml response.

        :raise ChannelInfoParsingError: if there is any issue with the parsing

        :return: {{'id': str, 'name': str, 'uri': str}
        """
        bs = BeautifulSoup(xml, 'xml')
        author = bs.find('author')
        if author:
            return {  # Raise here seems quite impossible
                'id': channel_id,
                'name': author.find('name').getText(),
                'url': author.find('uri').getText()
            }

        raise self.ChannelInfoParsingError(channel_id)

    def get_video_list(self, channel_id: str, use_cache: bool = False) -> list[dict]:
        """
        Gets a dictionary with Video information from a Channel's id.

        If use_cache is True, use the cached XML instead of a GET request.

        :raise YTUrl404: if YT returns 404
        :raise YTUrlUnexpectedStatusCode: if YT returns something else than 404
        :raise GettingError : if there is any other requests error

        :raises CacheDoesNotHaveKey: If there is no cache under key channel_id when use_cache == True

        :raises VideoListParsingError: If there is a missing key on the XML

        :return: [{'id': str, 'channel_id': str, 'name': str, 'url': str, 'pubdate': str, 'description': str,
        'thumbnail': str}]
        """
        if not use_cache:
            xml = self._get_url(self._rss_base_url % channel_id)
        else:
            try:
                xml = self.cache[channel_id]
            except KeyError:
                raise self.CacheDoesNotHaveKey(channel_id)

        return self._extract_video_information_from_xml(xml, channel_id)

    def get_video_list_multiple(self, channel_ids: list[str]) -> dict[str, list[dict]]:
        """
        Gets a video list for multiple Channel id's

        :raise YTUrl404: if YT returns 404
        :raise YTUrlUnexpectedStatusCode: if YT returns something else than 404
        :raise GettingError : if there is any other requests error

        :raises VideoListParsingError: If there is a missing key on the XML

        :return dict: {channel_id: [{'id': str, 'channel_id': str, 'name': str, 'url': str, 'pubdate': str,
        'description': str, 'thumbnail': str}]}
        """
        url_list = [self._rss_base_url % c for c in channel_ids]
        xml_to_url_names = self._get_urls_parallel(url_list)
        result = {}
        for key in xml_to_url_names.keys():
            result[key] = self._extract_video_information_from_xml(xml_to_url_names[key], key)
        return result

    def _extract_video_information_from_xml(self, xml: str, channel_id: str):
        """
        Extract video information from a https://www.youtube.com/feeds/videos.xml?channel_id=
        query's xml response.

        :raises VideoListParsingError: If there is a missing key on the XML

        :return: [{'id': str, 'channel_id': str, 'name': str, 'url': str, 'pubdate': str, 'description': str,
        'thumbnail': str}]
        """
        bs = BeautifulSoup(xml, 'xml')
        entries = bs.findAll('entry')
        videos = []
        for entry in entries:
            try:
                videos.append({  # Raise here seems quite impossible
                    'id': entry.find('yt:videoId').getText(),
                    'channel_id': channel_id,
                    'name': entry.find('title').getText(),
                    'url': entry.find('link').get('href'),
                    'pubdate': entry.find('published').getText(),
                    'description': entry.find('media:group').find('media:description').getText(),
                    'thumbnail': entry.find('media:group').find('media:thumbnail').get('url'),
                })
            except AttributeError:
                raise self.VideoListParsingError(channel_id)

        return videos

    def _get_url(self, url: str) -> str:
        """
        Wraps and translates calls to self.scrap_wrapper.make_unique_query()

        :raise YTUrl404: if YT returns 404
        :raise YTUrlUnexpectedStatusCode: if YT returns something else than 404
        :raise GettingError : if there is any other requests error
        """
        try:
            response = self.scrap_wrapper.make_unique_query(url)

        except InvalidStatusCode as exception:
            if exception.args[1] == 404:
                raise self.YTUrl404(url) from exception
            raise self.YTUrlUnexpectedStatusCode(exception.args) from exception

        except ReqHandlerError as exception:
            raise self.GettingError(exception) from exception
        else:
            return response.text

    def _get_urls_parallel(self, url_list: list[str]) -> dict[str, str]:
        """
        Wraps and translates calls to self.scrap_wrapper.make_bulk_queries()

        :raise YTUrl404: if YT returns 404
        :raise YTUrlUnexpectedStatusCode: if YT returns something else than 404
        :raise GettingError : if there is any other requests error

        :return dict: {channel_id: response}
        """
        res, errs = self.scrap_wrapper.make_bulk_queries(url_list)
        response = {}
        for r in res:
            key = r.url.split('channel_id=')[1]
            response[key] = r.text
        for e in errs:
            if e['error'] == InvalidStatusCode:
                if e['response'].status_code == 404:
                    raise self.YTUrl404(e['url'])
                raise self.YTUrlUnexpectedStatusCode(e)
            else:
                raise self.GettingError(e)
        return response

    class YTScraperError(Exception):
        """ Base exception for YTScraper errors """

    class CacheDoesNotHaveKey(YTScraperError):
        """ Attempted to access a cache key that does not exist """

    class UrlNotYT(YTScraperError):
        """ Input URL does not appear to be YT """

    class YTUrlNotSupported(YTScraperError):
        """ The URL is YT, but not supported by YTScraper """

    class GettingError(YTScraperError):
        """ Base errors for errors with getting """

    class YTUrl404(GettingError):
        """ YT URL returns 404 """

    class YTUrlUnexpectedStatusCode(GettingError):
        """ YT URL returns a http status other than 200 and 404 """

    class ParsingError(YTScraperError):
        """ Base errors for errors with parsing """

    class ChannelIDParsingError(ParsingError):
        """ Parsing error attempting to parse channel id """

    class ChannelThumbnailParsingError(ParsingError):
        """ Parsing error attempting to parse channel thumbnail """

    class ChannelInfoParsingError(ParsingError):
        """ Parsing error attempting to parse channel information """

    class VideoListParsingError(ParsingError):
        """ Parsing error attempting to parse video list """
