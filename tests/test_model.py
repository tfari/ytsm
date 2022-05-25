""" Tests for model """
from unittest import TestCase
from ytsm.model import Video

class TestVideoModel(TestCase):
    """ Video model tests """
    def test_sensible_pubdate(self):
        self.assertEqual('2020-11-21 17:47',
                         Video(idx='', channel_id='', name='', url='',
                               pubdate='2020-11-21T17:47:04+00:00',
                               description='', thumbnail='', new=True, watched=False).sensible_pubdate())
