import pathlib
from typing import Generic, TypeVar, cast


T = TypeVar("T")


class Data(Generic[T]):

    value: T
    # meta: Any

    def __init__(self, value: T) -> None:
        self.value = value

    @classmethod
    def from_file(cls, file: pathlib.Path):
        lines = file.read_text(encoding="utf-8").split("\n")

        # meta_lines: List[str] = [line for line in lines if line.find("#") == 0]

        data = [line for line in lines if line.find("#") == -1][0]

        if len(data) == 1:
            value = cast(T, data)
            return cls(value)
        else:
            return None
