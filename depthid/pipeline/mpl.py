import numpy as np
import matplotlib.style
import matplotlib as mpl
from matplotlib import pyplot as plt


mpl.style.use("dark_background")
mpl.rcParams['figure.figsize'] = [10.2, 7.5]
mpl.rcParams['figure.dpi'] = 60
mpl.rcParams['font.size'] = 12
mpl.rcParams['font.family'] = 'Consolas'
mpl.rcParams['legend.fontsize'] = 'large'
mpl.rcParams['figure.titlesize'] = 'large'


def plot_histogram(data: np.ndarray):
    fig = plt.figure()
    fig.tight_layout(pad=0)
    plot = fig.add_subplot(111)
    plt.title("Pixel Intensity")
    plt.xlabel("Intensity")
    plt.ylabel("# of Pixels")
    plt.yscale('log')
    plt.ylim(top=data.size)
    plot.plot(data)
    fig.canvas.draw()  # Big consumer

    d = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)  # 0
    d = d.reshape(fig.canvas.get_width_height()[::-1] + (3,))  # 0

    # Scale to uint16 space (65536)
    # todo: surely there must be a better way
    d = d.astype(np.uint16) / d.max() * 65536
    plt.close('all')
    return d


def plot_histogram_grey(data: np.ndarray, channel: int = 0, bins: int = 256,  min_v: int = 0,
                        max_v: int = 65536) -> np.ndarray:

    import cv2
    histr = cv2.calcHist([data], [channel], None, [bins], (min_v, max_v))
    fig = plt.figure()
    fig.tight_layout(pad=0)
    plot = fig.add_subplot(111)
    plt.title("Pixel Intensity")
    plt.xlabel("Intensity")
    plt.ylabel("# of Pixels")
    plt.yscale('log')
    plt.ylim(top=data.size)
    plot.plot(histr)
    fig.canvas.draw()

    d = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)

    # Scale to uint16 space (65536)
    # todo: surely there must be a better way
    d = d.astype(np.uint16) / d.max() * 65536

    d = d.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    plt.close('all')
    return d
