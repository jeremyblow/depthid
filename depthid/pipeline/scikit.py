import skimage
import numpy as np


def convert_uint8_uint16(data: np.ndarray, **state) -> np.ndarray:
    return skimage.img_as_uint(data)

