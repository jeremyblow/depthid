class Camera:

    features = {}
    settings = {}

    def __init__(self, camera_index: int, height: int, width: int, exposure_us: float, gain_db: float,
                 pixel_format: str, enabled: bool = True):
        """
        Arguments:
            camera_index (int): Index of camera, typically 0 to use default camera.
            height (int): Set vertical size of image, in pixels.
            width (int): Set horizontal size of image, in pixels.
        """
        self.camera_index = camera_index
        self.height = height
        self.width = width
        self.exposure_us = exposure_us
        self.gain_db = gain_db
        self.pixel_format = pixel_format
        self.enabled = enabled
        self.camera = None

    def initialize(self):
        raise NotImplementedError

    def set(self, key, value=None, perc=None):
        raise NotImplementedError

    def shutdown(self):
        raise NotImplementedError
