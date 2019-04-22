from .exception import ControllerException
from .grbl import Grbl
from .marlin import Marlin
from .motor import Motor
from .controller import Controller


def load_controller(**kwargs):
    return {
        'grbl': Grbl,
        'marlin': Marlin
    }[kwargs.pop('interface')](**kwargs)
