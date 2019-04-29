import numpy as np
import math
import skimage
from astropy.stats import sigma_clipped_stats
from astropy.visualization import SqrtStretch
from astropy.visualization.mpl_normalize import ImageNormalize
from photutils import CircularAperture, DAOStarFinder
from matplotlib import pyplot as plt

from depthid import red_rgb


# def sigma_clipped_stats(data: np.ndarray, sigma: float, max_iters: int = None, **state) -> np.ndarray:
#     """Calculate sigma-clipped statistics on the provided data.
#
#     Parameters below are from  http://docs.astropy.org/en/stable/api/astropy.stats.sigma_clipped_stats.html.
#
#     Arguments:
#         data (np.ndarray): Image ndarray.
#         max_iters (int): The maximum number of sigma-clipping iterations to perform or
#             None to clip until convergence is achieved (i.e., iterate until the last
#             iteration clips nothing). If convergence is achieved prior to maxiters
#             iterations, the clipping iterations will stop. The default is 5.
#         sigma (float): The number of standard deviations to use for both the lower and
#             upper clipping limit. These limits are overridden by sigma_lower and
#             sigma_upper, if input. The default is 3.
#         **state (dict): Receives DepthID job state.
#
#     Returns:
#         mean, median, std (tuple[float])
#     """
#     return sigma_clipped_stats(data, sigma=sigma, maxiters=max_iters)


def find_centroids(data: np.ndarray, sigma: float, max_iters: int = None, fwhm: float = 7.0, threshold: int = 2.3,
                   exclude_border: bool = False, ratio: float = .5, fwhm_range: set = None, **state) -> np.ndarray:
    """Find and plot centroids.

    Parameters below are from https://photutils.readthedocs.io/en/stable/api/photutils.DAOStarFinder.html
    and http://docs.astropy.org/en/stable/api/astropy.stats.sigma_clipped_stats.html.

    Resulting data set contains the following columns:
        'id', 'xcentroid', 'ycentroid', 'sharpness', 'roundness1', 'roundness2', 'npix', 'sky', 'peak', 'flux', 'mag'

    Arguments:
        data (np.ndarray): Image ndarray.
        max_iters (int): The maximum number of sigma-clipping iterations to perform or
            None to clip until convergence is achieved (i.e., iterate until the last
            iteration clips nothing). If convergence is achieved prior to maxiters
            iterations, the clipping iterations will stop. The default is 5.
        sigma (float): The number of standard deviations to use for both the lower and
            upper clipping limit. These limits are overridden by sigma_lower and
            sigma_upper, if input. The default is 3.
        threshold (float): The absolute image value above which to select sources.
        fwhm (float): The full-width half-maximum (FWHM) of the major axis of the Gaussian
            kernel in units of pixels.
        fwhm_range (tuple): Range (start, stop (exclusive), step) of FWHM's to go through. 
        exclude_border (bool): Set to True to exclude sources found within half the size
            of the convolution kernel from the image borders. The default is False, which
            is the mode used by DAOFIND.
        ratio (float): The ratio of the minor to major axis standard deviations of the
            Gaussian kernel. ratio must be strictly positive and less than or equal to
            1.0. The default is 1.0 (i.e., a circular Gaussian kernel).
        **state (dict): Receives DepthID job state.

    Returns:
        data (np.ndarray)

    Todo:
        Have circle radius match sqrt(npix / pi)
    """
    mean, median, std = sigma_clipped_stats(data, sigma=sigma, maxiters=max_iters)

    if not fwhm_range:
        fwhm_range = [fwhm]
    else:
        fwhm_range = range(*fwhm_range)

    source_cnt = 0

    fig = plt.figure()
    plt.title("Centroids")

    for fwhm in fwhm_range:
        daofind = DAOStarFinder(fwhm=fwhm, threshold=threshold * std, exclude_border=exclude_border, ratio=ratio)
        sources = daofind(data - median)
        if sources:
            source_cnt += len(sources)
            # Radii are constant for a given fwhm, use first
            CircularAperture(
                (sources['xcentroid'], sources['ycentroid']),
                r=np.sqrt(sources['npix'] / math.pi)[0]
            ).plot(color=red_rgb, lw=1.5, alpha=1.0)

    norm = ImageNormalize(stretch=SqrtStretch())
    plt.imshow(skimage.img_as_ubyte(data), cmap='gray', norm=norm)
    fnt_size = 14

    # Todo: offset is dependent on image dimensions
    h_offset = data.shape[0] * 1.065

    # Todo: height may be relative to window size
    t_height = data.shape[0] / fnt_size / 2
    plt.text(0, h_offset, f"Sigma: {sigma} Iters: {max_iters} FWHM: {fwhm} Threshold: {threshold}", fontsize=fnt_size)
    plt.text(0, h_offset + t_height, f"Mean: {mean:.2f} Median: {median:.2f} StdDev: {std:.2f}", fontsize=fnt_size)
    plt.text(0, h_offset + (t_height * 2), f"Sources: {source_cnt}", fontsize=fnt_size)
    fig.canvas.draw()
    
    d = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)  # 0
    d = d.reshape(fig.canvas.get_width_height()[::-1] + (3,))  # 0
    d = d.astype(np.uint16) / d.max() * 65536
    
    return d
