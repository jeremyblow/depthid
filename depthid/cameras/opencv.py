import cv2

from .camera import Camera
from .exception import CameraException


class OpenCV(Camera):

    capture_time = 0
    display_time = 0
    save_time = 0

    def initialize(self):
        """Initializes camera communication and capture parameters."""
        self.camera = cv2.VideoCapture(self.camera_index)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)

        if not self.camera.isOpened():
            raise CameraException("Camera initialization failed, verify camera is operational")
        return self.camera

    def capture(self):
        return self.camera.read()[1]

    @property
    def parameters(self):
        """Convenience function to return current camera properties."""
        return dict(
            format=self.camera.get(cv2.CAP_PROP_FORMAT),
            height=self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT),
            width=self.camera.get(cv2.CAP_PROP_FRAME_WIDTH),
            frame_rate=self.camera.get(cv2.CAP_PROP_FPS),
            brightness=self.camera.get(cv2.CAP_PROP_BRIGHTNESS),
            contrast=self.camera.get(cv2.CAP_PROP_CONTRAST),
            saturation=self.camera.get(cv2.CAP_PROP_SATURATION),
            hue=self.camera.get(cv2.CAP_PROP_HUE),
            gain=self.camera.get(cv2.CAP_PROP_GAIN),
            exposure=self.camera.get(cv2.CAP_PROP_EXPOSURE)
        )

    def shutdown(self):
        try:
            self.camera.release()
        except AttributeError:
            # Don't raise exception if camera is unset
            pass
