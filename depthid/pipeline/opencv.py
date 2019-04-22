import cv2
from numpy import ndarray


def display(data: ndarray, name: str = "DepthID", panel: str = "main"):
    # cv2.imshow(name, data)
    # todo: fix up
    return data


def gray_to_rgb(data: ndarray):
    return cv2.cvtColor(data, cv2.COLOR_GRAY2RGB)


def histogram_grey(data: ndarray, bin_count: int = 256):
    print(1111, data)
    return cv2.calcHist([data], [0], None, bin_count, [0, 65536])
