import rich.repr
from audio.config import IConfig


@rich.repr.auto
class FsRate(IConfig):
    _name_config: str = "n_fs"

    _value: float

    def __init__(self, value: float):
        self._value = value

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> float:
        return self._value


@rich.repr.auto
class PointsPerDecade(IConfig):
    _name_config: str = "points_per_decade"

    _value: float

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> float:
        return self._value


@rich.repr.auto
class NumberOfSamples(IConfig):
    _name_config: str = "number_of_samples"

    _value: int

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> int:
        return self._value


@rich.repr.auto
class FrequencyMin(IConfig):
    _name_config: str = "f_min"

    _value: float

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> float:
        return self._value


@rich.repr.auto
class FrequencyMax(IConfig):
    _name_config: str = "f_max"

    _value: float

    @property
    def name_config(self) -> str:
        return self._name_config

    @property
    def value(self) -> float:
        return self._value


@rich.repr.auto
class Sampling:

    _fs: FsRate
    _points_per_decade: PointsPerDecade
    _number_of_samples: NumberOfSamples
    _f_min: FrequencyMin
    _f_max: FrequencyMax

    def __init__(
        self,
        fs: float,
        points_per_decade: int,
        f_min: float,
        f_max: float,
    ) -> None:
        self._fs = FsRate(fs)
        self._points_per_decade = PointsPerDecade(points_per_decade)
        self._number_of_samples = NumberOfSamples(NumberOfSamples)
        self._f_min = FrequencyMin(f_min)
        self._f_max = FrequencyMax(f_max)

    @property
    def n_fs(self) -> float:
        return self._fs.value
