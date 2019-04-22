import numpy as np


def histogram(data: np.ndarray, bins: int = 256, range: tuple = (0, 65536)):
    return np.histogram(data.ravel(), bins, range)
