import cv2


class Camera:

    capture_time = 0
    display_time = 0
    save_time = 0

    def __init__(self, camera_index: int, height: int, width: int):
        """
        Arguments:
            camera_index (int): Index of camera, typically 0 to use default camera.
            height (int): Set vertical size of image, in pixels.
            width (int): Set horizontal size of image, in pixels.
        """
        self.camera_index = camera_index
        self.height = height
        self.width = width
        self.camera = None

    def initialize(self):
        """Initializes camera communication and capture parameters."""
        self.camera = cv2.VideoCapture(self.camera_index)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        return self.camera

    def capture(self):
        return self.camera.read()[1]

    def save(self, img, filename):
        cv2.imwrite(filename, img)

    def display(self, img):
        # waitKey helps primitive UI cycle through events
        cv2.imshow('frame', img)
        cv2.waitKey(1)

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
        self.camera.release()