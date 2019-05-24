import PySpin

from .camera import Camera
from .exception import CameraException


class Spinnaker(Camera):

    nodemap = None
    cam_list = None
    system = None
    image = None
    pixel_format = None
    type_map = {
        'Width': PySpin.CIntegerPtr,
        'Height': PySpin.CIntegerPtr,
        'ExposureAuto': PySpin.CEnumerationPtr,
        'ExposureTime': PySpin.CFloatPtr,
        'Gain': PySpin.CFloatPtr,
        'GainAuto': PySpin.CEnumerationPtr,
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
        
        # Camera may default to Auto, which prevents manual setting
        self.set_enum('ExposureAuto', 'Off')
        self.set_enum('GainAuto', 'Off')
        
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

        self.camera.BeginAcquisition()
        return self.camera

    def capture(self):
        self.image = self.camera.GetNextImage()
        self.image.Release()
        return self.image

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

    def shutdown(self):
        try:
            self.camera.EndAcquisition()
        except (AttributeError, PySpin.SpinnakerException):
            pass

        try:
            self.camera.DeInit()
        except AttributeError:
            pass

        del self.camera

        try:
            self.cam_list.Clear()
        except AttributeError:
            pass

        try:
            self.system.ReleaseInstance()
        except (AttributeError, PySpin.SpinnakerException):
            pass

    def __repr__(self):
        return f"{self.features.get('DeviceDisplayName', 'Spinnaker')}"
