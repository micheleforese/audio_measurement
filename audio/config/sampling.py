from typing import Optional
import rich.repr
from audio.console import console
from audio.config import Config_Dict, IConfig


@rich.repr.auto
class FrequencySampling(IConfig):
    name_config = "n_fs"

    _value: Optional[float]

    def __init__(self, value: Optional[float] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        fs = data.get_value([cls.name_config], float)

        if fs is not None:
            return cls(fs)
        else:
            return None

    def __rich_repr__(self):
        yield "Fs", self.value

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class PointsPerDecade(IConfig):
    name_config = "points_per_decade"

    _value: Optional[float]

    def __init__(self, value: Optional[float] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        points_per_decade = data.get_value([cls.name_config], float)

        if points_per_decade is not None:
            return cls(points_per_decade)
        else:
            return None

    def __rich_repr__(self):
        yield "Points per Decade", self.value

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class NumberOfSamples(IConfig):
    name_config = "number_of_samples"

    _value: Optional[int]

    def __init__(self, value: Optional[int] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        number_of_samples = data.get_value([cls.name_config], float)

        if number_of_samples is not None:
            return cls(number_of_samples)
        else:
            return None

    def __rich_repr__(self):
        yield "Number of samples", self.value

    @property
    def value(self) -> Optional[int]:
        return self._value

    @value.setter
    def value(self, value: Optional[int]):
        self._value = value


@rich.repr.auto
class FrequencyMin(IConfig):
    name_config = "f_min"

    _value: Optional[float]

    def __init__(self, value: Optional[float] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        f_min = data.get_value([cls.name_config], float)

        if f_min is not None:
            return cls(f_min)
        else:
            return None

    def __rich_repr__(self):
        yield "Frequency Min", self.value

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class FrequencyMax(IConfig):
    name_config = "f_max"

    _value: Optional[float]

    def __init__(self, value: Optional[float] = None):
        self._value = value

    @classmethod
    def from_dict(cls, data: Config_Dict):
        f_max = data.get_value([cls.name_config], float)

        if f_max is not None:
            return cls(f_max)
        else:
            return None

    def __rich_repr__(self):
        yield "Frequncy Max", self.value

    @property
    def value(self) -> Optional[float]:
        return self._value

    @value.setter
    def value(self, value: Optional[float]):
        self._value = value


@rich.repr.auto
class Sampling:
    name_config = "sampling"

    _fs: Optional[FrequencySampling]
    _points_per_decade: Optional[PointsPerDecade]
    _number_of_samples: Optional[NumberOfSamples]
    _f_min: Optional[FrequencyMin]
    _f_max: Optional[FrequencyMax]

    def __init__(
        self,
        fs: Optional[FrequencySampling] = None,
        points_per_decade: Optional[PointsPerDecade] = None,
        number_of_samples: Optional[NumberOfSamples] = None,
        f_min: Optional[FrequencyMin] = None,
        f_max: Optional[FrequencyMax] = None,
    ) -> None:

        self._fs = fs
        self._points_per_decade = points_per_decade
        self._number_of_samples = number_of_samples
        self._f_min = f_min
        self._f_max = f_max

    @classmethod
    def from_value(
        cls,
        fs: Optional[float] = None,
        points_per_decade: Optional[int] = None,
        number_of_samples: Optional[int] = None,
        f_min: Optional[float] = None,
        f_max: Optional[float] = None,
    ):
        fs = FrequencySampling(fs)
        points_per_decade = PointsPerDecade(points_per_decade)
        number_of_samples = NumberOfSamples(number_of_samples)
        f_min = FrequencyMin(f_min)
        f_max = FrequencyMax(f_max)

        return cls(
            fs,
            points_per_decade,
            number_of_samples,
            f_min,
            f_max,
        )

    @classmethod
    def from_config(cls, data: Config_Dict):
        sampling = Config_Dict(data.get_value([cls.name_config]))

        if sampling is not None:

            Fs = FrequencySampling.from_dict(sampling)
            points_per_decade = PointsPerDecade.from_dict(sampling)
            number_of_samples = NumberOfSamples.from_dict(sampling)
            f_min = FrequencyMin.from_dict(sampling)
            f_max = FrequencyMax.from_dict(sampling)

            return cls(
                Fs,
                points_per_decade,
                number_of_samples,
                f_min,
                f_max,
            )
        else:
            return None

    def override(
        self,
        fs: Optional[float] = None,
        points_per_decade: Optional[int] = None,
        number_of_samples: Optional[int] = None,
        f_min: Optional[float] = None,
        f_max: Optional[float] = None,
    ):
        if fs is not None:
            self.fs = fs

        if points_per_decade is not None:
            self.points_per_decade = points_per_decade

        if number_of_samples is not None:
            self.number_of_samples = number_of_samples

        if f_min is not None:
            self.f_min = f_min

        if f_max is not None:
            self.f_max = f_max

    @property
    def fs(self) -> Optional[float]:
        return self._fs.value

    @fs.setter
    def fs(self, value: Optional[float]):
        self._fs = value

    @property
    def points_per_decade(self) -> Optional[float]:
        return self._points_per_decade.value

    @points_per_decade.setter
    def points_per_decade(self, value: Optional[float]):
        self._points_per_decade = value

    @property
    def number_of_samples(self) -> Optional[int]:
        if self._number_of_samples is not None:
            return self._number_of_samples.value
        else:
            return None

    @number_of_samples.setter
    def number_of_samples(self, value: Optional[int]):
        self._number_of_samples = value

    @property
    def f_min(self) -> Optional[float]:
        return self._f_min.value

    @f_min.setter
    def f_min(self, value: Optional[float]):
        self._f_min = value

    @property
    def f_max(self) -> Optional[float]:
        return self._f_max.value

    @f_max.setter
    def f_max(self, value: Optional[float]):
        self._f_max = value
