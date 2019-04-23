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

g_cache = {}
np.seterr(divide='ignore')


def plot_histogram_fast(data: np.ndarray, log: str = "10", name: str = "1"):
    global g_cache

    try:
        data = {
            "e": np.log,
            "2": np.log2,
            "10": np.log10,
        }[log](data)
    except KeyError:
        pass

    if name not in g_cache:
        fig, ax = plt.subplots()
        plt.title("Pixel Intensity")
        plt.xlabel(f"Intensity ({len(data)} bin)")
        if log is not None:
            plt.ylabel(f"# of Pixels (log{log})")
        else:
            plt.ylabel("# of Pixels")
        line = ax.plot(data, animated=True)[0]
        fig.canvas.draw()
        background = fig.canvas.copy_from_bbox(ax.bbox)
        g_cache[name] = (fig, ax, line, background)
    else:
        fig, ax, line, background = g_cache[name]

    # Reset to empty region
    fig.canvas.restore_region(background)

    line.set_ydata(data)
    ax.draw_artist(line)
    fig.canvas.blit(ax.bbox)

    plt.close('all')

    d = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    d = d.reshape(fig.canvas.get_width_height()[::-1] + (3,))
    return d.astype(np.uint16) / d.max() * 65536


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

