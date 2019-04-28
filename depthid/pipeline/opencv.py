import cv2
import numpy as np


def histogram(data: np.ndarray, channel: int = 0, bins: int = 4196, min_v: int = 0, max_v: int = 65536, **state) -> np.array:
    """Generates histogram of pixel intensity for given channel.

    Arguments:
        data (np.ndarray): Image ndarray.
        channel (int): Color channel (0, for greyscale).
        bins (int): Number of equal-width bins.
        min_v (int): Minimum value.
        max_v (int): Maximum value.

    Returns:
        data (np.array): Histogram
    """
    # todo: mask for ROI
    return cv2.calcHist([data], [channel], None, [bins], (min_v, max_v))


def gray_to_rgb(data: np.ndarray, **state) -> np.ndarray:
    return cv2.cvtColor(data, cv2.COLOR_GRAY2RGB)


def save(data: np.ndarray, fn: str, **state):
    cv2.imwrite(fn, data)


def overlay_rectangle(data: np.ndarray, upper_left: tuple, lower_right: tuple, color: tuple = (58588, 13434, 48430),
                      **state) -> np.ndarray:
    """Overlay rectangle on image with border of specified color.

    Arguments:
        upper_left (tuple): (x_min, y_min) Coordinate for upper left corner of rectangle.
        lower_right (tuple): (x_max, y_max) Coordinate for lower right corner of rectangle.
        color (tuple): (red, green, blue) color (default: 58588, 13434, 48430).
        state (dict): Receives ignored state parameters.

    Returns:
        data (np.ndarray)
    """
    # Likely args will be provided as lists, case to tuples
    return cv2.rectangle(data, tuple(upper_left), tuple(lower_right), color)