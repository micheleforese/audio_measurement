import enum
from typing import Generic, Type, TypeVar

RangeType = TypeVar("RangeType")


class Range(Generic[RangeType]):
    _min: RangeType
    _max: RangeType

    def __init__(self, min: RangeType, max: RangeType) -> None:
        self._min = min
        self._max = max

    def __str__(self) -> str:
        return "{} to {}".format(self.min, self.max)

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
