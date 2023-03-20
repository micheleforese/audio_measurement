from __future__ import annotations

import typing
from datetime import datetime
from typing import Self

if typing.TYPE_CHECKING:
    from pathlib import Path


class SetLevel:
    set_level: float
    y_offset_db: float

    def __init__(self: Self, set_level: float, y_offset_db: float) -> None:
        self.set_level = set_level
        self.y_offset_db = y_offset_db

    @classmethod
    def from_file(cls: type[Self], file: Path) -> Self:
        if not file.exists() or not file.is_file():
            raise Exception("File does not Exists.")

        lines: list[str] = [
            line
            for line in file.read_text(encoding="utf-8").splitlines()
            if line.find("#") == -1  # Eliminate any comment or empty string
        ]

        set_level: float = float(lines[0])
        y_offset_db: float = float(lines[1])

        return cls(set_level=set_level, y_offset_db=y_offset_db)

    @classmethod
    def from_most_recent(
        cls: type[Self],
        directory: Path,
        file_path_pattern: str = "*.config.offset",
        file_name_pattern: str = r"%Y-%m-%d--%H-%M-%f",
    ) -> Self:
        if not directory.exists() or not directory.is_dir():
            raise Exception("Directory does not Exists.")

        set_level_file_list: list[Path] = list(directory.glob(file_path_pattern))

        if not (len(set_level_file_list) > 0):
            raise Exception("No file found.")

        set_level_file_list.sort(
            key=lambda name: datetime.strptime(
                name.name.strip(".")[0],
                file_name_pattern,
            ).astimezone(),
        )
        return cls.from_file(set_level_file_list[0])
