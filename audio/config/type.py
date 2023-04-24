from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar

if TYPE_CHECKING:
    from collections.abc import Generator


RangeType = TypeVar("RangeType")


class Range(Generic[RangeType]):
    _min: RangeType
    _max: RangeType

    def __init__(self: Self, min_value: RangeType, max_value: RangeType) -> None:
        self._min = min_value
        self._max = max_value

    def __str__(self: Self) -> str:
        return f"[{self.min_value} to {self.max_value}]"

    def __rich_repr__(self: Self) -> Generator[str, None, None]:
        yield self.__str__()

    @classmethod
    def from_list(
        cls: type[Self],
        data: tuple[RangeType, RangeType] | None,
    ) -> Self[RangeType] | None:
        if data is None:
            return None

        _min, _max = data

        return Self[RangeType](_min, _max)

    @property
    def min_value(self: Self) -> RangeType:
        return self._min

    @min_value.setter
    def min_value(self: Self, value: RangeType) -> None:
        self._min = value

    @property
    def max_value(self: Self) -> RangeType:
        return self._max

    @max_value.setter
    def max_value(self: Self, value: RangeType) -> None:
        self._max = value
