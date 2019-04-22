import cv2
import numpy as np


def histogram(data: np.ndarray, channel: int = 0, bins: int = 65536, min_v: int = 0, max_v: int = 65535) -> np.ndarray:
    """Generates histogram of pixel intensity for given channel.

    Arguments:
        data (np.ndarray): Image ndarray
        channel (int): Color channel (0, for greyscale)
        bins (int):
        min_v (int): Minimum value
        max_v (int): Maximum value

    Returns:
        data (np.ndarray): Histogram
    """
    # todo: mask for ROI
    # todo: document bins
    return cv2.calcHist([data], [channel], None, [bins], (min_v, max_v))


def gray_to_rgb(data: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(data, cv2.COLOR_GRAY2RGB)

