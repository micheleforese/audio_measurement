from datetime import datetime
import pathlib
from typing import List


class SetLevel:
    set_level: float
    y_offset_dB: float

    def __init__(self, file: pathlib.Path) -> None:

        if not file.exists() or not file.is_file():
            raise Exception("File does not Exists.")

        lines: List[str] = [
            line
            for line in file.read_text(encoding="utf-8").split("\n")
            if line.find("#") == -1  # Eliminate any comment
        ]

        if len(lines) != 2:
            raise Exception("Data must be 2 lines.")

        try:
            self.set_level = float(lines[0])
            self.y_offset_dB = float(lines[1])
        except Exception as e:
            raise e

    @classmethod
    def from_most_recent(
        cls,
        directory: pathlib.Path,
        file_path_pattern: str = "*.config.offset",
        file_name_pattern: str = r"%Y-%m-%d--%H-%M-%f",
    ):

        if not directory.exists() or not directory.is_dir():
            raise Exception("Directory does not Exists.")

        set_level_file_list = [
            set_level_file for set_level_file in directory.glob(file_path_pattern)
        ]

        if not (len(set_level_file_list) > 0):
            raise Exception("No file found.")

        set_level_file_list.sort(
            key=lambda name: datetime.datetime.strptime(
                name.name.strip(".")[0], file_name_pattern
            ),
        )
        return cls(set_level_file_list)
