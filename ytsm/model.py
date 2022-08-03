""" Model objects """
from dataclasses import dataclass

@dataclass
class Channel:
    """ Channel object """
    idx: str
    name: str
    url: str
    notify_on: bool = True

@dataclass
class Video:
    """ Video object """
    idx: str
    channel_id: str
    name: str
    url: str
    pubdate: str
    description: str
    thumbnail: str
    new: bool
    watched: bool

    def sensible_pubdate(self) -> str:
        """ Return smaller pubdate """
        date, time = self.pubdate.split('T')
        time = ':'.join(time.split(':')[:2])
        return f'{date} {time}'
