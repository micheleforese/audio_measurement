import pathlib
from typing import Self


class InsertionGain:
    insertion_gain_decibel: float

    def __init__(self: Self, file: pathlib.Path) -> None:
        if not file.exists() or not file.is_file():
            raise Exception("File does not Exists.")

        self.insertion_gain_decibel = float(file.read_text(encoding="utf-8"))
