""" Model objects """
from dataclasses import dataclass
from enum import Enum

class VideoStateType(Enum):
    """ State of Video """
    new = "New"
    unwatched = "Unwatched"
    old = "Old"
    all = "All"

@dataclass
class Channel:
    """ Channel object """
    idx: str
    name: str
    url: str
    notify_on: bool
    thumbnail: str

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


@dataclass
class BaseUpdateResponse:
    """ Base update response object """
    channel_id: str

@dataclass
class ErrorUpdateResponse(BaseUpdateResponse):
    """ Update response for errors """
    exception: Exception

@dataclass
class SuccessUpdateResponse(BaseUpdateResponse):
    """ Update response for successes """
    video_list: list[dict]


@dataclass
class MultipleUpdateResponse:
    """ Update response for multiple updates """
    successes: list[SuccessUpdateResponse]
    errors: list[ErrorUpdateResponse]
