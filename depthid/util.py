import json
import logging

from getch import getch


logger = logging.getLogger("depthid")


def pathify(path):
    """Normalizes path input to POSIX.

    Windows can interpret relative POSIX paths.
    """
    return path.replace('\\', '/').rstrip('/')


def load_config(config_fh):
    with config_fh as fh:
        return json.load(fh)


def to_csv(waypoint: dict):
    return ",".join(waypoint.values())


def get_key():
    key_map = {
        3: 'ctrl-c',
        27: 'escape',
        60: '<',
        62: '>',
        71: 'home',
        72: 'up',
        73: 'page_up',
        75: 'left',
        77: 'right',
        80: 'down',
        81: 'page_down',
        82: 'insert',
        83: 'delete'
    }

    # keyboard input may be sequence of two chars
    n = ord(getch())
    if n in (0, 224):
        return key_map.get(ord(getch()), None)
    else:
        return chr(n)


def log_dict(d, banner=None):
    max_key = max([len(k) for k in d]) + 1
    if banner:
        logger.info(f"----------- {banner} -----------")
    for k, v in d.items():
        logger.info(f"   {k:<{max_key}}: {v}")
