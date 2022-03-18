import pathlib
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple, Type, TypeVar

import pyjson5
from rich.tree import Tree

from cDAQ.console import console


def load_json_config(config_file_path):
    with open(config_file_path) as config_file:
        config = pyjson5.decode(config_file.read())

        console.print(config)

        return config


class Config_Dict:
    data: Any

    def __init__(self, data: Any) -> None:
        self.data = data

    T = TypeVar("T")

    def get_rvalue(
        self, path: List[str], type: Type[T] = Any, required: bool = True
    ) -> T:

        value: Any = self.data

        for p in path:
            try:
                value = value[p]
            except KeyError:
                console.print(
                    "Config [blue][{}][/blue] must be provided".format("/".join(path)),
                    style="error",
                )
                raise KeyError
                exit()

        return type(value)

    T = TypeVar("T")

    def get_value(
        self, path: List[str], type: Type[T] = Any, required: bool = True
    ) -> Optional[T]:
        value: Any = self.data

        for p in path:
            try:
                value = value[p]
            except KeyError:
                return None

        return type(value)


class IConfig_Class(ABC):

    _main_style: str
    _sub_property_style: str
    _sub_property_value_style: str

    _main_pattern: str
    _sub_pattern: str

    def __init__(
        self,
        main_style: str = "red",
        sub_property_style: str = "yellow",
        sub_property_value_style: str = "blue",
        main_pattern: str = r"[{0}]{1}[/{0}]:",
        sub_pattern: str = r"[{0}]{2}[/{0}]: [{1}]{3}[/{1}]",
    ) -> None:

        super().__init__()

        # Setup Properties
        self._main_style = main_style
        self._sub_property_style = sub_property_style
        self._sub_property_value_style = sub_property_value_style
        self._main_pattern = main_pattern
        self._sub_pattern = sub_pattern

        # Update the Pattern
        self._update_main_pattern()
        self._update_sub_pattern()

    @property
    def main_style(self):
        return self._main_style

    @main_style.setter
    def main_style(self, main_style):
        self._main_style = main_style
        self._update_main_pattern()

    @property
    def sub_property_style(self):
        return self._sub_property_style

    @sub_property_style.setter
    def sub_property_style(
        self,
        sub_property_style: str,
    ):
        self._sub_property_style = sub_property_style
        self._update_sub_pattern()

    @property
    def sub_property_value_style(self):
        return self._sub_property_value_style

    @sub_property_value_style.setter
    def sub_property_value_style(
        self,
        sub_property_value_style: str,
    ):
        self._sub_property_value_style = sub_property_value_style
        self._update_sub_pattern()

    @property
    def main_pattern(self):
        return self._main_pattern

    @main_pattern.setter
    def main_pattern(self, value):
        self._main_pattern = value

    @property
    def sub_pattern(self):
        return self._sub_pattern

    @sub_pattern.setter
    def sub_pattern(self, value):
        self._sub_pattern = value

    def _update_main_pattern(self):
        self.main_pattern = "[{0}]{1}[/{0}]:".format(self.main_style, "{}")

    def _update_sub_pattern(self):
        self.sub_pattern = "[{0}]{2}[/{0}]: [{1}]{3}[/{1}]".format(
            self.sub_property_style, self.sub_property_value_style, "{}", "{}"
        )

    @abstractmethod
    def init_from_config(self, data: Config_Dict):
        raise NotImplementedError

    def tree_pattern_main(self, *args: object) -> str:
        return self.main_pattern.format(*args)

    def tree_pattern_sub(self, *args: object) -> str:
        return self.sub_pattern.format(*args)

    @abstractmethod
    def set_tree_name(self, name: str):
        raise NotImplementedError

    @abstractmethod
    def get_tree_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def tree(self) -> Tree:
        raise NotImplementedError


class Rigol(IConfig_Class):
    _tree_name: str = "rigol"

    _amplitude_pp: Optional[float]

    def __init__(self, data: Optional[Config_Dict] = None) -> None:
        super().__init__()

        self.amplitude_pp = None

        if data:
            self.init_from_config(data)

    def init(self, amplitude_pp: float):
        self.amplitude_pp = amplitude_pp

    def init_from_config(self, data: Config_Dict):
        self.amplitude_pp = data.get_rvalue(["rigol", "amplitude_pp"], float)

    @property
    def amplitude_pp(self):
        return self._amplitude_pp

    @amplitude_pp.setter
    def amplitude_pp(self, amplitude_pp):
        self._amplitude_pp = amplitude_pp

    def get_tree_name(self) -> str:
        return self._tree_name

    def set_tree_name(self, name: str):
        self._tree_name = name

    def tree(self) -> Tree:
        tree = Tree(self.tree_pattern_main(self._tree_name))
        tree.add(
            self.tree_pattern_sub(
                "Amplitude pick-to-pick",
                self.amplitude_pp,
            )
        )

        return tree


class Nidaq(IConfig_Class):
    _tree_name: str = "nidaq"

    max_Fs: Optional[float]
    max_voltage: Optional[float]
    min_voltage: Optional[float]
    ch_input: Optional[str]

    def __init__(self, data: Optional[Config_Dict] = None) -> None:
        super().__init__()

        self.max_Fs = None
        self.max_voltage = None
        self.min_voltage = None
        self.ch_input = None

        if data:
            self.init_from_config(data)

    def init(
        self, max_Fs: float, max_voltage: float, min_voltage: float, ch_input: str
    ) -> None:
        self.max_Fs = max_Fs
        self.max_voltage = max_voltage
        self.min_voltage = min_voltage
        self.ch_input = ch_input

    def init_from_config(self, data: Config_Dict):
        self.max_Fs = data.get_rvalue(["nidaq", "max_Fs"], float)
        self.max_voltage = data.get_rvalue(["nidaq", "max_voltage"], float)
        self.min_voltage = data.get_rvalue(["nidaq", "min_voltage"], float)
        self.ch_input = data.get_rvalue(["nidaq", "ch_input"], str)

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self, name: str) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree(self.tree_pattern_main(self._tree_name))
        tree.add(self.tree_pattern_sub("Max Fs", self.max_Fs))
        tree.add(self.tree_pattern_sub("Max Voltage", self.max_voltage))
        tree.add(self.tree_pattern_sub("Min Voltage", self.min_voltage))
        tree.add(self.tree_pattern_sub("Input Channel", self.ch_input))

        return tree


class Sampling(IConfig_Class):
    _tree_name: str = "sampling"

    n_fs: Optional[float]
    points_per_decade: Optional[float]
    number_of_samples: Optional[int]
    f_min: Optional[float]
    f_max: Optional[float]

    def __init__(self, data: Optional[Config_Dict] = None) -> None:
        super().__init__()

        self.n_fs = None
        self.points_per_decade = None
        self.number_of_samples = None
        self.f_min = None
        self.f_max = None

        if data:
            self.init_from_config(data)

    def init(
        self,
        points_per_decade: float,
        number_of_samples: int,
        f_min: float,
        f_max: float,
        n_fs: Optional[float] = None,
    ):
        self.points_per_decade = points_per_decade
        self.number_of_samples = number_of_samples
        self.f_min = f_min
        self.f_max = f_max

        if n_fs:
            self.n_fs = n_fs

    def init_from_config(self, data: Config_Dict):

        n_fs_temp = data.get_value(["sampling", "n_fs"], float)
        if n_fs_temp:
            self.n_fs = n_fs_temp

        self.points_per_decade = data.get_rvalue(
            ["sampling", "points_per_decade"], float
        )
        self.number_of_samples = data.get_rvalue(["sampling", "number_of_samples"], int)
        self.f_min = data.get_rvalue(["sampling", "f_min"], float)
        self.f_max = data.get_rvalue(["sampling", "f_max"], float)

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree(self.tree_pattern_main(self._tree_name))
        tree.add(self.tree_pattern_sub("Points per Decade", self.points_per_decade))
        tree.add(self.tree_pattern_sub("Number of Samples", self.number_of_samples))
        tree.add(self.tree_pattern_sub("Min Hz", self.f_min))
        tree.add(self.tree_pattern_sub("Max Hz", self.f_max))

        return tree


class Plot(IConfig_Class):
    _tree_name: str = "plot"

    x_limit: Optional[Tuple[float, float]]
    y_limit: Optional[Tuple[float, float]]

    def __init__(self, data: Optional[Config_Dict] = None) -> None:
        super().__init__()

        self.x_limit = None
        self.y_limit = None

        if data:
            self.init_from_config(data)

    def init(
        self,
        x_limit: Optional[Tuple[float, float]] = None,
        y_limit: Optional[Tuple[float, float]] = None,
    ):
        self.x_limit = x_limit
        self.y_limit = y_limit

    def init_from_config(self, data: Config_Dict):

        if data.get_value(["plot"]):
            self.x_limit = data.get_value(["plot", "x_limit"], Tuple[float, float])
            self.y_limit = data.get_value(["plot", "y_limit"], Tuple[float, float])

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree(self.tree_pattern_main(self._tree_name))
        tree.add(
            self.tree_pattern_sub("x_limit", self.x_limit if self.x_limit else "Auto")
        )
        tree.add(
            self.tree_pattern_sub("y_limit", self.y_limit if self.y_limit else "Auto")
        )

        return tree


class Config:

    rigol: Optional[Rigol]
    nidaq: Optional[Nidaq]
    sampling: Optional[Sampling]
    plot: Optional[Plot]

    step: float

    def __init__(self) -> None:
        self.rigol = None
        self.nidaq = None
        self.sampling = None
        self.plot = None

    def from_file(self, config_file_path: pathlib.Path):
        self._init_config_from_file(Config_Dict(load_json_config(config_file_path)))

    def _init_config_from_file(self, data: Config_Dict):

        # Rigol Class
        self.rigol = Rigol(data)

        # Nidaq Class
        self.nidaq = Nidaq(data)

        # Sampling Class
        self.sampling = Sampling(data)

        # Plot Class
        self.plot = Plot(data)

        # Calculations
        self.calculate_step()

    def validate(self) -> bool:
        return False

    def calculate_step(self) -> float:
        self.step = 1 / self.sampling.points_per_decade
        return self.step

    def tree(self) -> Tree:
        tree = Tree("Configuration JSON", style="bold")

        tree.add(self.rigol.tree())
        tree.add(self.nidaq.tree())
        tree.add(self.sampling.tree())
        if self.plot:
            tree.add(self.plot.tree())

        return tree

    def print(self):
        console.print(self.tree())
