from typing import Optional, Tuple

import rich.repr

from audio.config import Config_Dict, IConfig
from audio.config.type import Range


@rich.repr.auto
class YOffset(IConfig):
    name_config = "y_offset"

    _value: Optional[float]

    def __rich_repr__(self):
        yield "y_offset", self.value if self.value else "None"

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

    def __rich_repr__(self):
        yield "x_limit", self.value if self.value else "None"

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

    def __rich_repr__(self):
        yield "y_limit", self.value if self.value else "None"

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
class InterpolationRate(IConfig):
    name_config = "interpolation_rate"

    _value: Optional[float]

    def __rich_repr__(self):
        yield "interpolation_rate", self.value if self.value else "None"

    def __init__(self, value: Optional[float] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        interpolation_rate = data.get_value([cls.name_config], float)

        if interpolation_rate is not None:
            return cls(interpolation_rate)
        else:
            return None

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class DPIResolution(IConfig):
    name_config = "dpi"

    _value: Optional[int]

    def __rich_repr__(self):
        yield "dpi", self.value if self.value else "None"

    def __init__(self, value: Optional[int] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        dpi = data.get_value([cls.name_config], int)

        if dpi is not None:
            return cls(dpi)
        else:
            return None

    @property
    def value(self) -> Optional[int]:
        return self._value

    @value.setter
    def value(self, value: Optional[int]):
        self._value = value


@rich.repr.auto
class Plot:
    name_config = "plot"

    _y_offset: Optional[YOffset]
    _x_limit: Optional[LimitXAxis]
    _y_limit: Optional[LimitYAxis]
    _interpolation_rate: Optional[InterpolationRate]
    _dpi: Optional[DPIResolution]

    def __rich_repr__(self):
        if self._y_offset:
            yield self._y_offset

        if self._x_limit:
            yield self._x_limit

        if self._y_limit:
            yield self._y_limit

        if self._interpolation_rate:
            yield self._interpolation_rate

        if self._dpi:
            yield self._dpi

    def __init__(
        self,
        y_offset: Optional[YOffset] = None,
        x_limit: Optional[LimitXAxis] = None,
        y_limit: Optional[LimitYAxis] = None,
        interpolation_rate: Optional[InterpolationRate] = None,
        dpi: Optional[DPIResolution] = None,
    ) -> None:
        self._y_offset = y_offset
        self._x_limit = x_limit
        self._y_limit = y_limit
        self._interpolation_rate = interpolation_rate
        self._dpi = dpi

    @classmethod
    def from_value(
        cls,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
        interpolation_rate: Optional[float] = None,
        dpi: Optional[int] = None,
    ):
        y_offset = YOffset(y_offset)
        x_limit = LimitXAxis(y_offset)
        y_limit = LimitYAxis(y_limit)
        interpolation_rate = InterpolationRate(interpolation_rate)
        dpi = DPIResolution(dpi)

        return cls(
            y_offset,
            x_limit,
            y_limit,
            interpolation_rate,
            dpi,
        )

    @classmethod
    def from_config(cls, data: Config_Dict):
        plot = Config_Dict.from_dict(data.get_value([cls.name_config]))

        if plot is not None:

            y_offset = YOffset.from_dict(plot)
            x_limit = LimitXAxis.from_dict(plot)
            y_limit = LimitYAxis.from_dict(plot)
            interpolation_rate = InterpolationRate.from_dict(plot)
            dpi = DPIResolution.from_dict(plot)

            return cls(
                y_offset,
                x_limit,
                y_limit,
                interpolation_rate,
                dpi,
            )
        else:
            return None

    def override(
        self,
        y_offset: Optional[float] = None,
        x_limit: Optional[Range[float]] = None,
        y_limit: Optional[Range[float]] = None,
        interpolation_rate: Optional[float] = None,
        dpi: Optional[int] = None,
    ):
        if y_offset is not None:
            self.y_offset = y_offset

        if x_limit is not None:
            self.x_limit = x_limit

        if y_limit is not None:
            self.y_limit = y_limit

        if interpolation_rate is not None:
            self._interpolation_rate = interpolation_rate

        if dpi is not None:
            self._dpi = dpi

    @property
    def y_offset(self) -> Optional[float]:
        if self._y_offset:
            return self._y_offset.value

    @y_offset.setter
    def y_offset(self, value: Optional[float]):
        self._y_offset = value

    @property
    def x_limit(self) -> Optional[Range[float]]:
        if self._x_limit:
            return self._x_limit.value

    @x_limit.setter
    def x_limit(self, value: Optional[Range[float]]):
        self._x_limit = value

    @property
    def y_limit(self) -> Optional[Range[float]]:
        if self._y_limit:
            return self._y_limit.value

    @y_limit.setter
    def y_limit(self, value: Optional[Range[float]]):
        self._y_limit = value

    @property
    def interpolation_rate(self) -> Optional[float]:
        if self._interpolation_rate:
            return self._interpolation_rate.value

    @interpolation_rate.setter
    def interpolation_rate(self, value: Optional[float]):
        self._interpolation_rate = value

    @property
    def dpi(self) -> Optional[int]:
        if self._dpi:
            return self._dpi.value

    @dpi.setter
    def dpi(self, value: Optional[int]):
        self._dpi = value
