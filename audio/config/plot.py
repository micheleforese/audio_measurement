from typing import Optional, Tuple

import rich.repr

from audio.config import Config_Dict, IConfig
from audio.config.type import Range


@rich.repr.auto
class YOffset(IConfig):
    name_config = "y_offset"

    _value: Optional[float]

    def __init__(self, value: Optional[float] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        y_offset = data.get_value([cls.name_config], float)
        if y_offset is not None:
            return cls(y_offset)
        else:
            return None

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class LimitXAxis(IConfig):
    name_config = "x_limit"

    _value: Optional[Range[float]]

    def __init__(self, value: Optional[Range[float]] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        x_limit = data.get_value([cls.name_config], Tuple[float, float])

        if x_limit is not None:
            return cls(Range(*x_limit))
        else:
            return None

    @property
    def value(self) -> Optional[Range[float]]:
        return self._value

    @value.setter
    def value(self, value: Optional[Range[float]]):
        self._value = value


@rich.repr.auto
class LimitYAxis(IConfig):
    name_config = "y_limit"

    _value: Optional[Range[float]]

    def __init__(self, value: Optional[Range[float]] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        y_limit = data.get_value([cls.name_config], Tuple[float, float])

        if y_limit is not None:
            return cls(Range(*y_limit))
        else:
            return None

    @property
    def value(self) -> Optional[Range[float]]:
        return self._value

    @value.setter
    def value(self, value: Optional[Range[float]]):
        self._value = value


@rich.repr.auto
class Plot:
    name_config = "plot"

    _y_offset: Optional[YOffset]
    _x_limit: Optional[LimitXAxis]
    _y_limit: Optional[LimitYAxis]

    def __init__(
        self,
        y_offset: Optional[YOffset] = None,
        x_limit: Optional[LimitXAxis] = None,
        y_limit: Optional[LimitYAxis] = None,
    ) -> None:
        self._y_offset = y_offset
        self._x_limit = x_limit
        self._y_limit = y_limit

    @classmethod
    def from_value(
        cls,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
    ):
        y_offset = YOffset(y_offset)
        x_limit = LimitXAxis(y_offset)
        y_limit = LimitYAxis(y_limit)

        return cls(
            y_offset,
            x_limit,
            y_limit,
        )

    @classmethod
    def from_config(cls, data: Config_Dict):
        plot = Config_Dict(data.get_value([cls.name_config]))

        if plot is not None:

            y_offset = YOffset.from_dict(plot)
            x_limit = LimitXAxis.from_dict(plot)
            y_limit = LimitYAxis.from_dict(plot)
            return cls(
                y_offset,
                x_limit,
                y_limit,
            )
        else:
            return None

    def override(
        self,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
    ):
        if y_offset is not None:
            self.y_offset = y_offset

        if x_limit is not None:
            self.x_limit = x_limit

        if y_limit is not None:
            self.y_limit = y_limit

    @property
    def y_offset(self) -> Optional[float]:
        return self._y_offset.value

    @y_offset.setter
    def y_offset(self, value: Optional[float]):
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
