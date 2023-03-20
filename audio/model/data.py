import pathlib
from typing import Generic, Self, TypeVar, cast

T = TypeVar("T")


class Data(Generic[T]):
    value: T

    def __init__(self: Self, value: T) -> None:
        self.value = value

    @classmethod
    def from_file(cls: type[Self], file: pathlib.Path) -> Self | None:
        lines: list[str] = file.read_text(encoding="utf-8").split("\n")

        data: str = [line for line in lines if line.find("#") == -1][0]

        if len(data) != 1:
            return None

        value = cast(T, data)
        return cls(value)
