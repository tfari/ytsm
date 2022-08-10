""" Image handling for VideoDetailBox instances """
import io
import requests
import threading
from typing import Callable

from PIL import Image, ImageTk, ImageDraw, ImageOps

from ytsm.uis.ytsm_controller import YTSMController

class ImagesHandler:
    """
    Class that handles image getting, caches, and default images for both Channels and Videos, to be used by
    VideoDetailBox instances.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.video_img_cache = {}
        self.channel_img_cache = {}

        # Circular mask for Channel thumbnails
        self.circular_mask = Image.new('L', (200, 200))
        ImageDraw.ImageDraw(self.circular_mask).ellipse((0, 0) + self.circular_mask.size, fill=255)
        self.circular_mask = self.circular_mask.resize((50, 50), Image.Resampling.LANCZOS)
        self.default_channel_image = None
        self.default_video_image = None

    def instantiate_default_images(self):
        """ This method serves as a proxy singleton-like instantiation of our default images. We can't instantiate
        them on __init__ because we are making this class a singleton via IMAGES_HANDLER and that means the class will
        get instantiated before root widget gets created. """
        if self.default_video_image is None and self.default_channel_image is None:  # Ensure only runs once
            self.default_video_image = ImageTk.PhotoImage(Image.new('1', (250, 250)))
            self.default_channel_image = ImageOps.fit(Image.new('L', (75, 75)), self.circular_mask.size,
                                                      centering=(0.5, 0.5))
            self.default_channel_image = ImageTk.PhotoImage(self.default_channel_image)

    def clear_caches(self):
        """ Clear both caches """
        with self.lock:
            self.video_img_cache = {}
            self.channel_img_cache = {}

    def id_in_cache(self, idx: str, cache_dict: dict) -> bool:
        """ Return if idx exists as a key in cache_dict """
        with self.lock:
            return idx in cache_dict

    def get_id_in_cache(self, idx: str, cache_dict: dict) -> ImageTk.PhotoImage:
        """ Get idx in cache_dict """
        with self.lock:
            return cache_dict.get(idx)

    def __thumbnail_get(self, using_cache: dict, default_img: ImageTk.PhotoImage, img_process_func: Callable,
                        object_id: str, thumbnail_url: str):
        """ Perform a thumbnail_url request """

        # If last saved image is the default one, pop it to attempt to get it again.
        with self.lock:
            if using_cache.get(object_id) == default_img:
                using_cache.pop(object_id)
            # If it is not, return None if it exists in the cache, as that means we already have the right image.
            elif object_id in using_cache:
                return None

        try:
            raw_data = requests.get(thumbnail_url)
            if raw_data.status_code != 200:
                # raise NotImplementedError("Request returned other than 200")  # TODO: Log statuscode + url info
                img = default_img
            else:
                img = Image.open(io.BytesIO(raw_data.content))
                img = img_process_func(img)
        except requests.RequestException:  # TODO Log if its not a max-retries signaling connection failure
            img = default_img

        with self.lock:
            using_cache[object_id] = img

    @staticmethod
    def __video_image_processing(img: Image) -> ImageTk.PhotoImage:
        """ Process image for video thumbnails """
        return ImageTk.PhotoImage(img.resize((250, 250)))

    def __channel_image_processing(self, img: Image) -> ImageTk.PhotoImage:
        """ Process image for channel thumbnails """
        img = ImageOps.fit(img.resize((75, 75)), self.circular_mask.size, centering=(0.5, 0.5))
        img.putalpha(self.circular_mask)
        return ImageTk.PhotoImage(img)

    def video_thumbnail_get(self, video_dto: YTSMController.VideoDTO) -> None:
        """ Get a Video's thumbnail and save it on self.video_img_cache """
        self.__thumbnail_get(self.video_img_cache, self.default_video_image, self.__video_image_processing,
                             video_dto.video.idx, video_dto.video.thumbnail)

    def channel_thumbnail_get(self, channel_dto: YTSMController.ChannelDTO) -> None:
        """ Get a Channel's thumbnail and save it on self.channel_img_cache """
        self.__thumbnail_get(self.channel_img_cache, self.default_channel_image, self.__channel_image_processing,
                             channel_dto.channel.idx, channel_dto.channel.thumbnail)


IMAGES_HANDLER = ImagesHandler()
