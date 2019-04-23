from .camera import Camera
from .exception import CameraException
from .opencv import OpenCV
from .spinnaker import Spinnaker


def load_camera(**kwargs):
    return {
        'spinnaker': Spinnaker,
        'opencv': OpenCV
    }[kwargs.pop('interface')](**kwargs)