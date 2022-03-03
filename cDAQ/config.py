from abc import ABC, abstractmethod
from asyncio.windows_events import NULL
from audioop import add
from optparse import Option
from typing import Any, List, Optional
from cDAQ.console import console
import jstyleson
from rich.table import Table, Column
from rich.tree import Tree
from rich.panel import Panel
from rich.syntax import Syntax
from pathlib import Path
import pyjson5


def load_json_config(config_file_path):
    with open(config_file_path) as config_file:
        # config = jstyleson.loads(config_file.read())
        config = pyjson5.decode(config_file.read())

        console.print(config)

        return config


class IConfig_Class(ABC):
    @abstractmethod
    def set_tree_name(self, name: str):
        raise Exception("NotImplementedException")

    @abstractmethod
    def get_tree_name(self) -> str:
        raise Exception("NotImplementedException")

    @abstractmethod
    def tree(self) -> Tree:
        raise Exception("NotImplementedException")


class Nidaq(IConfig_Class):
    _tree_name: str = "nidaq"

    max_voltage: float
    min_voltage: float
    ch_input: str

    def __init__(self, max_voltage: float, min_voltage: float, ch_input: str) -> None:
        self.max_voltage = max_voltage
        self.min_voltage = min_voltage
        self.ch_input = ch_input

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self, name: str) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree("[red]{}[/]:".format(self._tree_name))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Max Voltage", self.max_voltage))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Min Voltage", self.min_voltage))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Input Channel", self.ch_input))

        return tree


class Sampling(IConfig_Class):
    _tree_name: str = "sampling"

    points_per_decade: int
    min_Hz: float
    max_Hz: float
    amplitude_pp: float

    def __init__(
        self,
        points_per_decade: int,
        min_Hz: float,
        max_Hz: float,
        amplitude_pp: float,
    ):
        self.points_per_decade = points_per_decade
        self.min_Hz = min_Hz
        self.max_Hz = max_Hz
        self.amplitude_pp = amplitude_pp

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self, name: str) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree("[red]{}[/]:".format(self._tree_name))
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format(
                "Points per Decade", self.points_per_decade
            )
        )
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Min Hz", self.min_Hz))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Max Hz", self.max_Hz))
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format(
                "Amplitude pick-to-pick", self.amplitude_pp
            )
        )

        return tree


class Limits(IConfig_Class):
    _tree_name: str = "limits"

    delay_min: float
    aperture_min: float
    interval_min: float

    def __init__(self, delay_min: float, aperture_min: float, interval_min: float):
        self.delay_min = delay_min
        self.aperture_min = aperture_min
        self.interval_min = interval_min

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree("[red]{}[/]:".format(self._tree_name))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Delay min", self.delay_min))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Aperture min", self.aperture_min))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Interval min", self.interval_min))

        return tree


class Plot(IConfig_Class):
    _tree_name: str = "plot"

    x_limit = Optional[List[float]]
    y_limit = Optional[List[float]]

    def __init__(
        self,
        x_limit: Optional[List[float]] = None,
        y_limit: Optional[List[float]] = None,
    ):
        self.x_limit = x_limit
        self.y_limit = y_limit

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree("[red]{}[/]:".format(self._tree_name))
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format(
                "x_limit", self.x_limit if self.x_limit != None else "None"
            )
        )
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format(
                "y_limit", self.y_limit if self.y_limit != None else "None"
            )
        )

        return tree


class Config:
    row_data: Any

    number_of_samples: int
    Fs: float
    amplitude_pp: float
    nidaq: Nidaq
    sampling: Sampling
    limits: Limits
    plot: Plot

    step: float

    def __init__(self, config_file_path: Path) -> None:
        self.row_data = load_json_config(config_file_path)
        self._init_config()

    def _init_config(self):

        self.number_of_samples = int(self.row_data["number_of_samples"])
        self.Fs = float(self.row_data["Fs"])
        self.amplitude_pp = float(self.row_data["amplitude_pp"])

        try:
            nidaq_max_voltage = float(self.row_data["nidaq"]["max_voltage"])
        except KeyError:
            code = Syntax(
                'nidaq_max_voltage = float(self.row_data["nidaq"]["max_voltage"])',
                "python",
                theme="monokai",
            )
            console.print(Panel(code), style="error")
            console.print("nidaq/max_voltage must be provided", style="error")

        # Nidaq Class
        self.nidaq = Nidaq(
            max_voltage=nidaq_max_voltage,
            min_voltage=float(self.row_data["nidaq"]["min_voltage"]),
            ch_input=str(self.row_data["nidaq"]["ch_input"]),
        )

        # Sampling Class
        self.sampling = Sampling(
            points_per_decade=int(self.row_data["sampling"]["points_per_decade"]),
            min_Hz=float(self.row_data["sampling"]["min_Hz"]),
            max_Hz=float(self.row_data["sampling"]["max_Hz"]),
            amplitude_pp=float(self.row_data["sampling"]["amplitude_pp"]),
        )

        # Limits Class
        self.limits = Limits(
            delay_min=float(self.row_data["limits"]["delay_min"]),
            aperture_min=float(self.row_data["limits"]["aperture_min"]),
            interval_min=float(self.row_data["limits"]["interval_min"]),
        )

        plot_x_limit: Optional[List[float]] = None
        plot_y_limit: Optional[List[float]] = None

        try:
            plot_x_limit = self.row_data["plot"]["x_limit"]
        except KeyError:
            plot_x_limit = None

        try:
            plot_y_limit = self.row_data["plot"]["y_limit"]
        except KeyError:
            plot_y_limit = None

        # Plot Class
        self.plot = Plot(
            x_limit=plot_x_limit,
            y_limit=plot_y_limit,
        )

        # Calculations
        self.step = 1 / self.sampling.points_per_decade

    def tree(self) -> Tree:
        tree = Tree("Configuration JSON", style="bold")
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format(
                "number of samples", self.number_of_samples
            )
        )
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format("Sampling Frequency (Fs)", self.Fs)
        )
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format(
                "Amplitude pick-to-pick", self.amplitude_pp
            )
        )

        tree.add(self.nidaq.tree())
        tree.add(self.sampling.tree())
        tree.add(self.limits.tree())
        tree.add(self.plot.tree())

        return tree

    def print(self) -> None:
        console.print(Panel.fit(self.tree()))
