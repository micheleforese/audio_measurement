from pathlib import Path
from typing import List
import matplotlib.pyplot as plt


class Plot:
    def __init__(self) -> None:
        pass

    def generate_plot(
        plot_file_path: Path,
        x: List[float],
        y: List[float],
        xscale: str,
        title: str,
        xlabel: str,
        ylabel: str,
        ylim: List[float],
    ):
        plt.plot(x, y)
        plt.xscale(xscale)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.ylim(ylim[0], ylim[1])
        plt.savefig(plot_file_path.name)
