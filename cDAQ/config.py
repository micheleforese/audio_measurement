from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Optional

import pyjson5
from rich.panel import Panel
from rich.tree import Tree

from cDAQ.console import console


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

    def __init__(
        self,
        points_per_decade: int,
        min_Hz: float,
        max_Hz: float,
    ):
        self.points_per_decade = points_per_decade
        self.min_Hz = min_Hz
        self.max_Hz = max_Hz

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

        try:
            self.number_of_samples = int(self.row_data["number_of_samples"])
        except KeyError:
            console.print("Config number_of_samples must be provided", style="error")
            exit()

        try:
            self.Fs = float(self.row_data["Fs"])
        except KeyError:
            console.print("Config Fs must be provided", style="error")
            exit()

        try:
            self.amplitude_pp = float(self.row_data["amplitude_pp"])
        except KeyError:
            console.print("Config amplitude_pp must be provided", style="error")
            exit()

        # Nidaq Class
        try:
            nidaq_max_voltage = float(self.row_data["nidaq"]["max_voltage"])
        except KeyError:
            console.print("Config nidaq/max_voltage must be provided", style="error")
            exit()

        try:
            nidaq_min_voltage = float(self.row_data["nidaq"]["min_voltage"])
        except KeyError:
            console.print("Config nidaq/min_voltage must be provided", style="error")
            exit()

        try:
            nidaq_ch_input = str(self.row_data["nidaq"]["ch_input"])
        except KeyError:
            console.print("Config nidaq/ch_input must be provided", style="error")
            exit()

        self.nidaq = Nidaq(
            max_voltage=nidaq_max_voltage,
            min_voltage=nidaq_min_voltage,
            ch_input=nidaq_ch_input,
        )

        # Sampling Class
        try:
            sampling_points_per_decade = int(
                self.row_data["sampling"]["points_per_decade"]
            )
        except KeyError:
            console.print(
                "Config sampling/points_per_decade must be provided", style="error"
            )
            exit()

        try:
            sampling_min_Hz = float(self.row_data["sampling"]["min_Hz"])
        except KeyError:
            console.print("Config sampling/min_Hz must be provided", style="error")
            exit()

        try:
            sampling_max_Hz = float(self.row_data["sampling"]["max_Hz"])
        except KeyError:
            console.print("Config sampling/max_Hz must be provided", style="error")
            exit()

        self.sampling = Sampling(
            points_per_decade=sampling_points_per_decade,
            min_Hz=sampling_min_Hz,
            max_Hz=sampling_max_Hz,
        )

        # Limits Class
        try:
            limits_delay_min = float(self.row_data["limits"]["delay_min"])
        except KeyError:
            console.print("Config limits/delay_min must be provided", style="error")
            exit()

        try:
            limits_aperture_min = float(self.row_data["limits"]["aperture_min"])
        except KeyError:
            console.print("Config limits/aperture_min must be provided", style="error")
            exit()

        try:
            limits_interval_min = float(self.row_data["limits"]["interval_min"])
        except KeyError:
            console.print("Config limits/interval_min must be provided", style="error")
            exit()

        self.limits = Limits(
            delay_min=limits_delay_min,
            aperture_min=limits_aperture_min,
            interval_min=limits_interval_min,
        )

        try:
            plot_x_limit: Optional[List[float]] = self.row_data["plot"]["x_limit"]
        except KeyError:
            plot_x_limit = None

        try:
            plot_y_limit: Optional[List[float]] = self.row_data["plot"]["y_limit"]
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
