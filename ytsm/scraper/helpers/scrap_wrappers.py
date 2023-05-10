from ytsm.scraper.helpers import req_handler

"""
Wrapper class for using req_handler when scraping
"""


class ScrapWrapper(object):
    def __init__(self, headers):
        self.headers = headers

    def dict_to_url(self, dict_query, base_url):
        """
        Transform a dictionary of key: value into an URL query of ?key=value&key2=value2, etc

        :param dict_query: dict, str: str
        :param base_url: str, base of the url to append the query to

        :return: str, base of the url + '?' + dict_query
        """

        query_url = base_url + '?'

        count = 0
        for key in dict_query.keys():
            if count == 0:
                query_url += '%s=%s' % (str(key), str(dict_query.get(key)))
            else:
                query_url += '&%s=%s' % (str(key), str(dict_query.get(key)))
            count += 1

        return query_url

    def make_bulk_queries(self, query_list, *, allow_errors=True, n_threads=10, n_passes=5, sleep_pass=2, headers=True):
        """
        Wraps bulk threaded queries.

        :param query_list: list, strs with urls to query
        :param allow_errors: bool, should scraping allow errors, default to True
        :param n_threads: int, number of threads to use
        :param n_passes: int, number of passes to do when there are errors
        :param sleep_pass: int, time to sleep between passes

        :return: list, [responses, errors] : [list, list]
        """

        headers = self.headers if headers is True else None

        TRH = req_handler.ThreadedRequestHandler(query_list,
                                                 req_handler.RequestData(req_handler.GET, headers=headers),
                                                 req_handler.RequestErrorData(allow_errors=allow_errors,
                                                                              expected_status_codes=[200]),
                                                 thread_num=n_threads, max_passes=n_passes, sleep_pass=sleep_pass)
        TRH.do_threads()

        return TRH.responses, TRH.errors

    def make_bulk_posts_single(self, query_list, *, data, allow_errors=True, n_threads=10, n_passes=5, sleep_pass=2):
        """
        Wraps bulk threaded posts with a single payload.

        :param query_list: list, strs with urls to query
        :param data: str, data to pass through
        :param allow_errors: bool, should scraping allow errors, default to True
        :param n_threads: int, number of threads to use
        :param n_passes: int, number of passes to do when there are errors
        :param sleep_pass: int, time to sleep between passes

        :return: list, [responses, errors] : [list, list]
        """

        TRH = req_handler.ThreadedRequestHandler(query_list,
                                                 req_handler.RequestData(req_handler.POST, headers=self.headers,
                                                                         data=data),
                                                 req_handler.RequestErrorData(allow_errors=allow_errors,
                                                                              expected_status_codes=[200, 201]),
                                                 thread_num=n_threads, max_passes=n_passes, sleep_pass=sleep_pass)
        TRH.do_threads()

        return TRH.responses, TRH.errors

    def make_unique_query(self, query_url, *, allow_errors=False, headers=True):
        """
        Wraps making an unique query.

        Lets request_handler errors propagate up.

        :param query_url: str, url to query
        :param allow_errors: bool, should scraping allow errors, default to False

        :raise req_handler Exceptions: lets Exceptions propagate to the caller.
        :return: list, responses
        """
        headers = self.headers if headers is True else None
        
        RH = req_handler.RequestHandler([query_url], req_handler.RequestData(req_handler.GET, headers=headers),
                                        req_handler.RequestErrorData(allow_errors=allow_errors,
                                                                     expected_status_codes=[200]))

        RH.run()

        return RH.responses[0]

    def make_unique_post(self, query_url, data, *, allow_errors=False, headers=True):
        """
        Wraps making a unique post.

        Lets request_handler errors propagate up.

        :param query_url: str, url to query
        :param data: dict

        :param allow_errors: bool, should scraping allow errors, default to False
        :param headers: dict

        :raise req_handler Exceptions: lets Exceptions propagate to the caller.
        :return: list, responses
        """
        headers = self.headers if headers is True else None

        RH = req_handler.RequestHandler([query_url], req_handler.RequestData(req_handler.POST, headers=headers,
                                                                             data=data),
                                        req_handler.RequestErrorData(allow_errors=allow_errors,
                                                                     expected_status_codes=[200]))

        RH.run()

        return RH.responses[0]
