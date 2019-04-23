import numpy as np


def histogram(data: np.ndarray, bins: int = 4192, min_v: int = 0, max_v: int = 65536):
    return np.histogram(data.ravel(), bins, (min_v, max_v))[0]
