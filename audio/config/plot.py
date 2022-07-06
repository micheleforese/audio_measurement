from typing import Optional, Union

import rich.repr

from audio.config import IConfig
from audio.config.type import ModAuto, Range


@rich.repr.auto
class YOffset(IConfig):
    _name_config: str = "y_offset"

    _value: Optional[Union[float, ModAuto]]

    def __init__(self, value: Optional[Union[float, ModAuto]]):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> Optional[Union[float, ModAuto]]:
        return self._value

    @value.setter
    def value(self, value: Optional[Union[float, ModAuto]]):
        self._value = value


@rich.repr.auto
class LimitXAxis(IConfig):
    _name_config: str = "x_limit"

    _value: Optional[Range[float]]

    def __init__(self, value: Optional[Range[float]]):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> Optional[Range[float]]:
        return self._value

    @value.setter
    def value(self, value: Optional[Range[float]]):
        self._value = value


@rich.repr.auto
class LimitYAxis(IConfig):
    _name_config: str = "y_limit"

    _value: Optional[Range[float]]

    def __init__(self, value: Optional[Range[float]]):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> Optional[Range[float]]:
        return self._value

    @value.setter
    def value(self, value: Optional[Range[float]]):
        self._value = value


@rich.repr.auto
class Plot:
    _name_config: str = "plot"

    _y_offset: YOffset
    _x_limit: LimitXAxis
    _y_limit: LimitYAxis

    def __init__(
        self,
        y_offset: Optional[Union[float, ModAuto]] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
    ) -> None:
        self._y_offset = YOffset(y_offset)
        self._x_limit = LimitXAxis(x_limit)
        self._y_limit = LimitYAxis(y_limit)

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def y_offset(self) -> Optional[Union[float, ModAuto]]:
        return self._y_offset.value

    @y_offset.setter
    def y_offset(self, value: Optional[Union[float, ModAuto]]):
        self._y_offset = value

    @property
    def x_limit(self) -> Optional[Range[float]]:
        return self._x_limit.value

    @x_limit.setter
    def x_limit(self, value: Optional[Range[float]]):
        self._x_limit = value

    @property
    def y_limit(self) -> Optional[Range[float]]:
        return self._y_limit.value

    @y_limit.setter
    def y_limit(self, value: Optional[Range[float]]):
        self._y_limit = value
