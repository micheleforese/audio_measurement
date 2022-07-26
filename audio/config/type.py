from __future__ import annotations

import enum
from typing import Generic, List, TypeVar, overload

from audio.type import Option

RangeType = TypeVar("RangeType")


class Range(Generic[RangeType]):
    _min: RangeType
    _max: RangeType

    def __init__(self, min: RangeType, max: RangeType) -> None:
        self._min = min
        self._max = max

    def __str__(self) -> str:
        return f"[{self.min} to {self.max}]"

    def __rich_repr__(self) -> str:
        yield self.__str__()

    @classmethod
    def from_list(cls, range: Option[List[RangeType]]) -> Option[Range[RangeType]]:

        if not range.is_null:
            if len(range) != 2:
                raise Exception("Range must be 2.")

            return Option[Range](Range[RangeType](range[0], range[1]))

        return Option[List[RangeType]].null()

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
