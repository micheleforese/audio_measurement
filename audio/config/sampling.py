from typing import Optional
import rich.repr
from audio.config import IConfig


@rich.repr.auto
class FrequencySampling(IConfig):
    _name_config: str = "n_fs"

    _value: Optional[float]

    def __init__(self, value: Optional[float]):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class PointsPerDecade(IConfig):
    _name_config: str = "points_per_decade"

    _value: Optional[float]

    def __init__(self, value: Optional[float]):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class NumberOfSamples(IConfig):
    _name_config: str = "number_of_samples"

    _value: Optional[int]

    def __init__(self, value: Optional[int]):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> Optional[int]:
        return self._value

    @value.setter
    def value(self, value: Optional[int]):
        self._value = value


@rich.repr.auto
class FrequencyMin(IConfig):
    _name_config: str = "f_min"

    _value: Optional[float]

    def __init__(self, value: Optional[float]):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class FrequencyMax(IConfig):
    _name_config: str = "f_max"

    _value: Optional[float]

    def __init__(self, value: Optional[float]):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class Sampling:
    _name_config: str = "sampling"

    _fs: FrequencySampling
    _points_per_decade: PointsPerDecade
    _number_of_samples: NumberOfSamples
    _f_min: FrequencyMin
    _f_max: FrequencyMax

    def __init__(
        self,
        fs: Optional[float] = None,
        points_per_decade: Optional[int] = None,
        number_of_samples: Optional[int] = None,
        f_min: Optional[float] = None,
        f_max: Optional[float] = None,
    ) -> None:
        self._fs = FrequencySampling(fs)
        self._points_per_decade = PointsPerDecade(points_per_decade)
        self._number_of_samples = NumberOfSamples(number_of_samples)
        self._f_min = FrequencyMin(f_min)
        self._f_max = FrequencyMax(f_max)

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def fs(self) -> Optional[float]:
        return self._fs.value

    @fs.setter
    def fs(self, value: Optional[float]):
        self._fs = value

    @property
    def points_per_decade(self) -> Optional[float]:
        return self._fs.value

    @points_per_decade.setter
    def points_per_decade(self, value: Optional[float]):
        self._points_per_decade = value

    @property
    def number_of_sample(self) -> Optional[int]:
        return self._fs.value

    @number_of_sample.setter
    def number_of_sample(self, value: Optional[int]):
        self._number_of_sample = value

    @property
    def f_min(self) -> Optional[float]:
        return self._fs.value

    @f_min.setter
    def f_min(self, value: Optional[float]):
        self._f_min = value

    @property
    def f_max(self) -> Optional[float]:
        return self._fs.value

    @f_max.setter
    def f_max(self, value: Optional[float]):
        self._f_max = value
