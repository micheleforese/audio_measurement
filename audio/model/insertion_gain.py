from datetime import datetime
import pathlib
from typing import List
from audio.console import console


class InsertionGain:
    y_offset_dB: float

    def __init__(self, file: pathlib.Path) -> None:

        if not file.exists() or not file.is_file():
            raise Exception("File does not Exists.")

        self.y_offset_dB = float(file.read_text(encoding="utf-8"))
