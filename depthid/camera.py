import cv2
import PySpin


class CameraException(Exception):
    pass


def load_camera(**kwargs):
    return {
        'spinnaker': PySpinCamera,
        'opencv': OpenCVCamera
    }[kwargs.pop('interface')](**kwargs)


class Camera:

    features = {}
    settings = {}

    def __init__(self, camera_index: int, height: int, width: int, exposure_us: float, gain_db: float,
                 pixel_format: str, display_format: str, save_formats: list, enabled: bool = True):
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
        self.display_format = display_format
        self.save_formats = save_formats
        self.enabled = enabled
        self.camera = None

    def initialize(self):
        raise NotImplementedError

    def acquire(self, filename=None):
        img = self.capture()
        if self.display_format:
            self.display(img)
        if filename:
            self.save(img, filename)

    def capture(self):
        raise NotImplementedError

    def display(self, data):
        # waitKey helps primitive UI cycle through events
        cv2.imshow('frame', data)
        cv2.waitKey(1)

    def set(self, key, value=None, perc=None):
        raise NotImplementedError

    def save(self, img, filename):
        raise NotImplementedError

    def shutdown(self):
        raise NotImplementedError

    @property
    def parameters(self):
        return dict()


class OpenCVCamera(Camera):

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

    def save(self, img, filename):
        for save_format in self.save_formats:
            fn = f"{filename}.{save_format}"
            cv2.imwrite(fn, img)

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


class PySpinCamera(Camera):

    nodemap = None
    cam_list = None
    system = None
    image = None
    pixel_format = None
    type_map = {
        'Width': PySpin.CIntegerPtr,
        'Height': PySpin.CIntegerPtr,
        'ExposureTime': PySpin.CFloatPtr,
        'Gain': PySpin.CFloatPtr,
        'AcquisitionMode': PySpin.CEnumerationPtr,
        'PixelFormat': PySpin.CEnumerationPtr
    }

    def initialize(self):
        self.system = PySpin.System.GetInstance()

        # todo: Allow explicit specification
        self.cam_list = self.system.GetCameras()
        for camera in self.cam_list:
            try:
                camera.Init()
            except PySpin.SpinnakerException:
                pass
            else:
                self.camera = camera
                break
        else:
            raise CameraException("No valid camera found")

        self.get_transport_features()

        self.nodemap = self.camera.GetNodeMap()
        self.get_camera_features()
        self.set_enum('AcquisitionMode', 'Continuous')
        self.set("Width", self.width)
        self.set("Height", self.height)
        self.set("ExposureTime", self.exposure_us)
        self.set("Gain", self.gain_db)

        # Get newest image only
        s_node_map = self.camera.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
        handling_mode_entry = handling_mode.GetEntryByName('NewestOnly')
        handling_mode.SetIntValue(handling_mode_entry.GetValue())

        # Set pixel format
        try:
            self.set_enum("PixelFormat", self.pixel_format.replace(' ', ''))
            self.pixel_format = getattr(PySpin, f"PixelFormat_{self.pixel_format.replace(' ', '')}")
        except AttributeError:
            raise CameraException(f"Invalid pixel format: {self.pixel_format}")

        self.display_format = getattr(PySpin, f"PixelFormat_{self.display_format.replace(' ', '')}")

        self.camera.BeginAcquisition()
        return self.camera

    def capture(self):
        self.image = self.camera.GetNextImage()
        self.image.Release()
        return self.image

    def display(self, data):
        cv2.imshow('frame', self.image.Convert(self.display_format, PySpin.HQ_LINEAR).GetNDArray())
        # waitKey helps primitive UI cycle through events
        cv2.waitKey(1)

    def get_transport_features(self):
        """Obtains device information from transport layer."""
        nodemap = self.camera.GetTLDeviceNodeMap()
        info = PySpin.CCategoryPtr(nodemap.GetNode("DeviceInformation"))
        for feature in info.GetFeatures():
            node_feature = PySpin.CValuePtr(feature)
            try:
                self.features[node_feature.GetName()] = node_feature.ToString()
            except PySpin.SpinnakerException:
                self.features[node_feature.GetName()] = None

    def get_camera_features(self):
        for f, f_type in self.type_map.items():
            if f_type is not PySpin.CEnumerationPtr:
                node = f_type(self.nodemap.GetNode(f))
                self.features[f"{f}Min"] = node.GetMin()
                self.features[f"{f}Max"] = node.GetMax()
                self.features[f"{f}Range"] = self.features[f"{f}Max"] - self.features[f"{f}Min"]
                self.settings[f] = node.GetValue()
                self.settings[f"{f}%"] = (self.settings[f] - self.features[f"{f}Min"]) / self.features[f"{f}Range"]
            else:
                node = f_type(self.nodemap.GetNode(f))
                self.features[f"{f}Choices"] = ",".join([e.GetDisplayName() for e in node.GetEntries()])
                self.settings[f] = node.GetCurrentEntry().GetDisplayName()

    def set(self, key, value=None, perc=None):
        if value is not None:
            value = max(self.features[f"{key}Min"], min(value, self.features[f"{key}Max"]))
        elif perc is not None:
            perc = min(1.0, max(0, perc))
            value = (self.features[f"{key}Range"] * perc) + self.features[f"{key}Min"]

        node = self.type_map[key](self.nodemap.GetNode(key))
        # Normal for some values to be quantized
        node.SetValue(value)
        self.get_camera_features()
        return self.settings[key]

    def set_enum(self, key, value):
        node = self.type_map[key](self.nodemap.GetNode(key))
        entry = node.GetEntryByName(value)

        try:
            node.SetIntValue(entry.GetValue())
        except AttributeError:
            raise CameraException(f"Invalid {key} setting: {value}")

        self.get_camera_features()
        return self.settings[key]

    def save(self, data, filename):
        for save_format in self.save_formats:
            fn = f"{filename}.{save_format}"
            self.image.Save(fn)

    def shutdown(self):
        try:
            self.camera.EndAcquisition()
        except PySpin.SpinnakerException:
            pass

        self.camera.DeInit()
        del self.camera
        self.cam_list.Clear()

        try:
            self.system.ReleaseInstance()
        except PySpin.SpinnakerException:
            pass

    def __repr__(self):
        return f"{self.features.get('DeviceDisplayName', 'Spinnaker')}"
