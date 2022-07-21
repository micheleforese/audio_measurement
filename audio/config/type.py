import enum
from typing import Generic, List, Tuple, TypeVar, overload
import rich

from audio.type import Option

RangeType = TypeVar("RangeType")


class Range(Generic[RangeType]):
    _min: RangeType
    _max: RangeType

    @overload
    def __init__(self, min: RangeType, max: RangeType) -> None:
        self._min = min
        self._max = max

    @overload
    def __init__(self, range: Tuple[float, float]) -> None:
        _min, _max = range

        self._min = _min
        self._max = _max

    @overload
    def __init__(self, range: List[float]) -> None:
        self._min = range[0]
        self._max = range[1]

    def __str__(self) -> str:
        return f"[{self.min} to {self.max}]"

    def __rich_repr__(self) -> str:
        yield f"[{self.min} to {self.max}]"

    @classmethod
    def from_tuple(
        cls, range: Option[Tuple[float, float]]
    ) -> Option[Tuple[float, float]]:
        if not range.is_null:
            return Option[Tuple[Range]](Range(range))

        return Option[Tuple[float, float]].null()

    @property
    def min(self) -> RangeType:
        return self._min

    @min.setter
    def min(self, value: RangeType):
        self._min = value

    @property
    def max(self) -> RangeType:
        return self._max

    @max.setter
    def max(self, value: RangeType):
        self._max = value


class ModAuto(enum.Enum):
    NO = "no"
    MIN = "min"
    MAX = "max"

    def __str__(self) -> str:
        return "{}".format(self.name)
