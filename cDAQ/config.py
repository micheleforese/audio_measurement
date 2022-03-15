from abc import ABC, abstractmethod
from curses.ascii import FS
from pathlib import Path
import pathlib
from typing import Any, List, Optional, Tuple

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


class Rigol(IConfig_Class):
    _tree_name: str = "rigol"

    amplitude_pp: float

    def __init__(self, amplitude_pp: float) -> None:
        self.amplitude_pp = amplitude_pp

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self, name: str) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree("[red]{}[/]:".format(self._tree_name))
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format(
                "Amplitude pick-to-pick", self.amplitude_pp
            )
        )

        return tree


class Nidaq(IConfig_Class):
    _tree_name: str = "nidaq"

    max_Fs: float
    max_voltage: float
    min_voltage: float
    ch_input: str

    def __init__(
        self, max_Fs: float, max_voltage: float, min_voltage: float, ch_input: str
    ) -> None:
        self.max_Fs = max_Fs
        self.max_voltage = max_voltage
        self.min_voltage = min_voltage
        self.ch_input = ch_input

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self, name: str) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree("[red]{}[/]:".format(self._tree_name))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Max Fs", self.max_Fs))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Max Voltage", self.max_voltage))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Min Voltage", self.min_voltage))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Input Channel", self.ch_input))

        return tree


class Sampling(IConfig_Class):
    _tree_name: str = "sampling"

    points_per_decade: float
    number_of_samples: int
    min_Hz: float
    max_Hz: float

    def __init__(
        self,
        points_per_decade: float,
        number_of_samples: int,
        min_Hz: float,
        max_Hz: float,
    ):
        self.points_per_decade = points_per_decade
        self.number_of_samples = number_of_samples
        self.min_Hz = min_Hz
        self.max_Hz = max_Hz

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree("[red]{}[/]:".format(self._tree_name))
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format(
                "Points per Decade", self.points_per_decade
            )
        )
        tree.add(
            "[yellow]{}[/]: [blue]{}[/]".format(
                "Number of Samples", self.number_of_samples
            )
        )
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Min Hz", self.min_Hz))
        tree.add("[yellow]{}[/]: [blue]{}[/]".format("Max Hz", self.max_Hz))

        return tree


class Plot(IConfig_Class):
    _tree_name: str = "plot"

    x_limit = Optional[Tuple[float, float]]
    y_limit = Optional[Tuple[float, float]]

    def __init__(
        self,
        x_limit: Optional[Tuple[float, float]] = None,
        y_limit: Optional[Tuple[float, float]] = None,
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

    rigol: Rigol
    nidaq: Nidaq
    sampling: Sampling
    plot: Optional[Plot] = None

    step: float

    def __init__(self) -> None:
        pass

    def from_file(self, config_file_path: pathlib.Path):
        load_json_config(config_file_path)
        self._init_config_from_file(load_json_config(config_file_path))

    def _init_config_from_file(self, data):

        # Rigol Class
        try:
            rigol_amplitude_pp = float(data["rigol"]["amplitude_pp"])
        except KeyError:
            console.print("Config rigol/amplitude_pp must be provided", style="error")
            exit()

        self.rigol = Rigol(rigol_amplitude_pp)

        # Nidaq Class
        try:
            nidaq_max_Fs = float(data["nidaq"]["max_Fs"])
        except KeyError:
            console.print("Config nidaq/max_Fs must be provided", style="error")
            exit()

        try:
            nidaq_max_voltage = float(data["nidaq"]["max_voltage"])
        except KeyError:
            console.print("Config nidaq/max_voltage must be provided", style="error")
            exit()

        try:
            nidaq_min_voltage = float(data["nidaq"]["min_voltage"])
        except KeyError:
            console.print("Config nidaq/min_voltage must be provided", style="error")
            exit()

        try:
            nidaq_ch_input = str(data["nidaq"]["ch_input"])
        except KeyError:
            console.print("Config nidaq/ch_input must be provided", style="error")
            exit()

        self.nidaq = Nidaq(
            max_Fs=nidaq_max_Fs,
            max_voltage=nidaq_max_voltage,
            min_voltage=nidaq_min_voltage,
            ch_input=nidaq_ch_input,
        )

        # Sampling Class
        try:
            sampling_points_per_decade = float(data["sampling"]["points_per_decade"])
        except KeyError:
            console.print(
                "Config sampling/points_per_decade must be provided", style="error"
            )
            exit()

        try:
            sampling_number_of_samples = int(data["number_of_samples"])
        except KeyError:
            console.print(
                "Config sampling/number_of_samples must be provided", style="error"
            )
            exit()

        try:
            sampling_min_Hz = float(data["sampling"]["min_Hz"])
        except KeyError:
            console.print("Config sampling/min_Hz must be provided", style="error")
            exit()

        try:
            sampling_max_Hz = float(data["sampling"]["max_Hz"])
        except KeyError:
            console.print("Config sampling/max_Hz must be provided", style="error")
            exit()

        self.sampling = Sampling(
            points_per_decade=sampling_points_per_decade,
            number_of_samples=sampling_number_of_samples,
            min_Hz=sampling_min_Hz,
            max_Hz=sampling_max_Hz,
        )

        # Plot Class
        try:
            plot_index: Optional[Any] = data["plot"]
        except KeyError:
            plot_index = None

        if plot_index:
            try:
                plot_x_limit: Optional[Tuple[float, float]] = data["plot"]["x_limit"]
            except KeyError:
                plot_x_limit = None

            try:
                plot_y_limit: Optional[Tuple[float, float]] = data["plot"]["y_limit"]
            except KeyError:
                plot_y_limit = None

            self.plot = Plot(
                x_limit=plot_x_limit,
                y_limit=plot_y_limit,
            )

        # Calculations
        self.step = 1 / self.sampling.points_per_decade

    def tree(self) -> Tree:
        tree = Tree("Configuration JSON", style="bold")

        tree.add(self.rigol.tree())
        tree.add(self.nidaq.tree())
        tree.add(self.sampling.tree())
        if self.plot:
            tree.add(self.plot.tree())

        return tree

    def print(self) -> None:
        console.print(Panel.fit(self.tree()))
