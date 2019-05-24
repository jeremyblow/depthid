import numpy as np
import skimage
from astropy.stats import sigma_clipped_stats
from astropy.visualization import SqrtStretch
from astropy.visualization.mpl_normalize import ImageNormalize
from photutils import CircularAperture, DAOStarFinder
from matplotlib import pyplot as plt

        
def find_centroids(data: np.ndarray, sigma: float, iters: int, fwhm: float, threshold: int):
    mean, median, std = sigma_clipped_stats(data, sigma=sigma, maxiters=iters)
    daofind = DAOStarFinder(fwhm=fwhm, threshold=threshold * std)
    sources = daofind(data - median)
    positions = sources['xcentroid'], sources['ycentroid']
    apertures = CircularAperture(positions, r=7.0)
    norm = ImageNormalize(stretch=SqrtStretch())
    
    fig = plt.figure()
    plt.title("Centroids")
    
    #plt.imshow(data, cmap='Greys', origin='lower', norm=norm)
    apertures.plot(color='blue', lw=1.5, alpha=0.5)
    plt.imshow(skimage.img_as_ubyte(data), cmap='gray', norm=norm)
    fnt_size = 14
    plt.text(0, 1320, f"Sigma: {sigma} Iters: {iters} FWHM: {fwhm} Threshold: {threshold}", fontsize=fnt_size)
    plt.text(0, 1380, f"Mean: {mean} Median: {median} StdDev: {std}", fontsize=fnt_size)
    plt.text(0, 1440, f"Sources: {len(sources)}", fontsize=fnt_size)
    fig.canvas.draw()
    
    d = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)  # 0
    d = d.reshape(fig.canvas.get_width_height()[::-1] + (3,))  # 0
    d = d.astype(np.uint16) / d.max() * 65536
    
    return d
    