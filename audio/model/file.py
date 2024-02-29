from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

import rich


@dataclass
@rich.repr.auto
class CacheFile:
    database: dict[str, Path] = field(default_factory=dict)

    def get(self: Self, key: str) -> Path | None:
        file: Path | None = self.database.get(key, None)
        return file

    def add(self: Self, key: str, path: Path) -> bool:
        if self.get(key) is None:
            self.database[key] = path
            return True
        return False


@dataclass
@rich.repr.auto
class File:
    key: str | None = None
    path: str | None = None

    def overload(self: Self, key: str | None, path: str | None) -> None:
        if key is not None:
            self.key = key
        if path is not None:
            self.path = path

    def is_null(self: Self) -> bool:
        return self.key is None and self.path is None
