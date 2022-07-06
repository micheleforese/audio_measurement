import pathlib
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Tuple, Type, TypeVar, Union, cast

import pyjson5
from rich.panel import Panel
from rich.tree import Tree

from audio.config.exception import (
    ConfigError,
    ConfigException,
    ConfigNoneValueError,
    ConfigNoneValueException,
)
from audio.config.type import ModAuto, Range
from audio.console import console


def load_json_config(config_file_path):
    with open(config_file_path, encoding="utf-8") as config_file:
        file_content: str = config_file.read()
        config = pyjson5.decode(file_content)
        return config


class NotInitializedWarning(RuntimeWarning):
    pass


class Config_Dict:
    data: Any

    def __init__(self, data: Any) -> None:
        self.data = data

    # TODO: Fix type overrride
    T = TypeVar("T")

    def get_rvalue(self, path: List[str], type_value: Type[T] = Any) -> T:

        value: Any = self.data

        for p in path:
            try:
                value = value[p]
            except KeyError:
                console.print(
                    "Config [blue][{}][/blue] must be provided".format("/".join(path)),
                    style="error",
                )
                exit()

        return cast(type_value, value)

    T = TypeVar("T")

    def get_value(self, path: List[str], type_value: Type[T] = Any) -> Optional[T]:
        value: Any = self.data

        for p in path:
            try:
                value = value[p]
            except KeyError:
                return None

        return cast(type_value, value)


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
    def validate(self) -> bool:
        raise NotImplementedError

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
        self.amplitude_pp = None

        super().__init__()

        if data:
            self.init_from_config(data)

    def init(self, amplitude_pp: float):
        self.amplitude_pp = amplitude_pp

    def init_from_config(self, data: Config_Dict):
        self.amplitude_pp = data.get_rvalue(["rigol", "amplitude_pp"], float)

    def validate(self) -> bool:
        if self._amplitude_pp:
            return False
        else:
            return True

    @property
    def amplitude_pp(self) -> float:
        if self._amplitude_pp:
            return self._amplitude_pp
        else:
            raise ConfigNoneValueException

    @amplitude_pp.setter
    def amplitude_pp(self, amplitude_pp: Optional[float]):
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

    _max_Fs: Optional[float]
    _max_voltage: Optional[float]
    _min_voltage: Optional[float]
    _ch_input: Optional[str]

    def __init__(self, data: Optional[Config_Dict] = None) -> None:
        self.max_Fs = None
        self.max_voltage = None
        self.min_voltage = None
        self.ch_input = None

        super().__init__()

        if data:
            self.init_from_config(data)

    def init(
        self, max_Fs: float, max_voltage: float, min_voltage: float, ch_input: str
    ) -> None:
        self._max_Fs = max_Fs
        self.max_voltage = max_voltage
        self.min_voltage = min_voltage
        self.ch_input = ch_input

    def init_from_config(self, data: Config_Dict):
        self.max_Fs = data.get_rvalue(["nidaq", "max_Fs"], float)
        self.max_voltage = data.get_rvalue(["nidaq", "max_voltage"], float)
        self.min_voltage = data.get_rvalue(["nidaq", "min_voltage"], float)
        self.ch_input = data.get_rvalue(["nidaq", "ch_input"], str)

    def validate(self) -> bool:
        if self._max_Fs and self._max_voltage and self.min_voltage and self.ch_input:
            return False
        else:
            return True

    @property
    def max_Fs(self) -> float:
        if self._max_Fs:
            return self._max_Fs
        else:
            raise ConfigNoneValueError

    @max_Fs.setter
    def max_Fs(self, value: Optional[float]):
        self._max_Fs = value

    @property
    def max_voltage(self) -> float:
        if self._max_voltage:
            return self._max_voltage
        else:
            raise ConfigNoneValueError

    @max_voltage.setter
    def max_voltage(self, value: Optional[float]):
        self._max_voltage = value

    @property
    def min_voltage(self) -> float:
        if self._min_voltage:
            return self._min_voltage
        else:
            raise ConfigNoneValueError

    @min_voltage.setter
    def min_voltage(self, value: Optional[float]):
        self._min_voltage = value

    @property
    def ch_input(self) -> str:
        if self._ch_input:
            return self._ch_input
        else:
            raise ConfigNoneValueError

    @ch_input.setter
    def ch_input(self, value: Optional[str]):
        self._ch_input = value

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree(self.tree_pattern_main(self._tree_name))
        tree.add(self.tree_pattern_sub("Max Fs", self._max_Fs))
        tree.add(self.tree_pattern_sub("Max Voltage", self.max_voltage))
        tree.add(self.tree_pattern_sub("Min Voltage", self.min_voltage))
        tree.add(self.tree_pattern_sub("Input Channel", self.ch_input))

        return tree


class Sampling(IConfig_Class):
    _tree_name: str = "sampling"

    _n_fs: Optional[float]
    _points_per_decade: Optional[float]
    _number_of_samples: Optional[int]
    _f_range: Optional[Range[float]]
    _f_min: Optional[float]
    _f_max: Optional[float]

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
        points_per_decade: Optional[float] = None,
        number_of_samples: Optional[int] = None,
        f_range: Optional[Range[float]] = None,
        n_fs: Optional[float] = None,
    ):
        self.points_per_decade = points_per_decade
        self.number_of_samples = number_of_samples
        self.f_range = f_range
        self.n_fs = n_fs

    def init_from_config(self, data: Config_Dict):

        n_fs_temp = data.get_value(["sampling", "n_fs"], float)
        if n_fs_temp:
            self.n_fs = n_fs_temp

        self.points_per_decade = data.get_rvalue(
            ["sampling", "points_per_decade"], float
        )
        self.number_of_samples = data.get_rvalue(["sampling", "number_of_samples"], int)
        f_min = data.get_rvalue(["sampling", "f_min"], float)
        f_max = data.get_rvalue(["sampling", "f_max"], float)

        self.f_range = Range(f_min, f_max)

    def validate(self) -> bool:
        if (
            self._points_per_decade
            and self._number_of_samples
            and self._f_range
            and self._n_fs
        ):
            return False
        else:
            return True

    @property
    def n_fs(self) -> float:
        if self._n_fs:
            return self._n_fs
        else:
            raise ConfigNoneValueException

    @n_fs.setter
    def n_fs(self, value: Optional[float]):
        self._n_fs = value

    @property
    def points_per_decade(self) -> float:
        if self._points_per_decade:
            return self._points_per_decade
        else:
            raise ConfigNoneValueException

    @points_per_decade.setter
    def points_per_decade(self, value: Optional[float]):
        self._points_per_decade = value

    @property
    def number_of_samples(self) -> int:
        if self._number_of_samples:
            return self._number_of_samples
        else:
            raise ConfigNoneValueException

    @number_of_samples.setter
    def number_of_samples(self, value: Optional[int]):
        self._number_of_samples = value

    @property
    def f_range(self) -> Range[float]:
        if self._f_range:
            return self._f_range
        else:
            raise ConfigNoneValueError

    @f_range.setter
    def f_range(self, value: Optional[Range[float]]):
        self._f_range = value

    def set_tree_name(self, name: str):
        self._tree_name = name

    def get_tree_name(self) -> str:
        return self._tree_name

    def tree(self) -> Tree:
        tree = Tree(self.tree_pattern_main(self._tree_name))
        tree.add(self.tree_pattern_sub("Points per Decade", self.points_per_decade))
        tree.add(self.tree_pattern_sub("Number of Samples", self.number_of_samples))
        tree.add(self.tree_pattern_sub("Frequency Min Hz", self.f_range.min))
        tree.add(self.tree_pattern_sub("Frequency Max Hz", self.f_range.max))

        return tree


class Plot(IConfig_Class):
    _tree_name: str = "plot"

    _y_offset: Optional[Union[float, ModAuto]]
    _x_limit: Optional[Range[float]]
    _y_limit: Optional[Range[float]]

    def __init__(self, data: Optional[Config_Dict] = None) -> None:
        super().__init__()

        self._y_offset = None
        self._x_limit = None
        self._y_limit = None

        if data:
            self.init_from_config(data)

    def init(
        self,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
        y_offset: Optional[Union[float, ModAuto]] = None,
    ):
        self.x_limit = x_limit
        self.y_limit = y_limit
        self.y_offset = y_offset

    def init_from_config(self, data: Config_Dict):

        if data.get_value(["plot"]):
            x_lim = data.get_value(["plot", "x_limit"], Tuple[float, float])
            self.x_limit = Range(*x_lim) if x_lim else None

            y_lim = data.get_value(["plot", "y_limit"], Tuple[float, float])
            self.y_limit = Range(*y_lim) if y_lim else None

            y_offset = data.get_value(["plot", "y_offset"], float)
            if y_offset:
                self.y_offset = y_offset
            else:
                y_offset_auto = data.get_value(["plot", "y_offset_auto"], str)
                if y_offset_auto:
                    if y_offset_auto == ModAuto.MIN.value:
                        self.y_offset = ModAuto.MIN
                    elif y_offset_auto == ModAuto.MAX.value:
                        self.y_offset = ModAuto.MAX
                    elif y_offset_auto == ModAuto.NO.value:
                        self.y_offset = ModAuto.NO
                    else:
                        raise ConfigError

    def validate(self) -> bool:
        return False

    @property
    def x_limit(self) -> Optional[Range[float]]:
        return self._x_limit

    @x_limit.setter
    def x_limit(self, value: Optional[Range[float]]):
        self._x_limit = value

    @property
    def y_limit(self) -> Optional[Range[float]]:
        return self._y_limit

    @y_limit.setter
    def y_limit(self, value: Optional[Range[float]]):
        self._y_limit = value

    @property
    def y_offset(self) -> Optional[Union[float, ModAuto]]:
        return self._y_offset

    @y_offset.setter
    def y_offset(self, value: Optional[Union[float, ModAuto]]):
        self._y_offset = value

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
        tree.add(
            self.tree_pattern_sub(
                "y_offset", self.y_offset if self.y_offset else "Auto"
            )
        )

        return tree


class Config:

    _rigol: Rigol
    _nidaq: Nidaq
    _sampling: Sampling
    _plot: Plot

    _step: float

    def __init__(self) -> None:
        self.rigol = Rigol()
        self.nidaq = Nidaq()
        self.sampling = Sampling()
        self.plot = Plot()

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

    def validate(self) -> bool:
        config_list: List[IConfig_Class] = [
            self.rigol,
            self.nidaq,
            self.sampling,
            self.plot,
        ]

        for v in config_list:
            if v.validate():
                return True
        return False

    @property
    def rigol(self):
        return self._rigol

    @rigol.setter
    def rigol(self, value: Rigol):
        self._rigol = value

    @property
    def nidaq(self):
        return self._nidaq

    @nidaq.setter
    def nidaq(self, value: Nidaq):
        self._nidaq = value

    @property
    def sampling(self):
        return self._sampling

    @sampling.setter
    def sampling(self, value: Sampling):
        self._sampling = value

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, value: Plot):

        self._plot = value

    @property
    def step(self) -> float:
        if self.sampling.points_per_decade:
            self._step = 1 / self.sampling.points_per_decade
        else:
            raise ConfigException
        return self._step

    def tree(self) -> Tree:
        tree = Tree("Configuration JSON", style="bold")

        tree.add(self.rigol.tree())
        tree.add(self.nidaq.tree())
        tree.add(self.sampling.tree())
        if self.plot:
            tree.add(self.plot.tree())

        return tree

    def print(self):
        console.print(Panel(self.tree(), title="Configuration JSON"))


class IConfig(ABC):
    @property
    @abstractmethod
    def name_config(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def value(self):
        raise NotImplementedError
