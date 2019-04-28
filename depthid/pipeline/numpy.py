import numpy as np


def histogram(data: np.ndarray, bins: int = 4192, min_v: int = 0, max_v: int = 65536, **state) -> np.array:
    """Generates histogram from flattened (1d) array of pixel intensity.

    Arguments:
        data (np.ndarray): Image ndarray.
        bins (int): Number of equal-width bins.
        min_v (int): Minimum value (inclusive).
        max_v (int): Maximum value (inclusive).

    Returns:
        data (np.array): Histogram values
    """
    return np.histogram(data.ravel(), bins, (min_v, max_v))[0]


def region_of_interest(data: np.ndarray, y_min: int, y_max: int, x_min: int, x_max: int, **state) -> np.ndarray:
    """Generates slice of image based on provided coordinate limits.

    Arguments:
        data (np.ndarray): Image ndarray.
        y_min (int): Minimum Y limit.
        y_max (int): Maximum Y limit.
        x_min (int): Minimum X limit.
        x_max (int): Maximum X limit.

    Returns:
        data (np.ndarray): Slice of image.
    """
    # todo: find out if +1 is needed
    return data[y_min:y_max + 1, x_min:x_max + 1]

