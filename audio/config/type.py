from __future__ import annotations

from typing import Generic, TypeVar


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
    def from_list(
        cls,
        range: list[RangeType] | None,
    ) -> Range[RangeType] | None:

        if range:
            if len(range) != 2:
                raise Exception("Range must be 2.")

            return Range[RangeType](range[0], range[1])

        return None

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
