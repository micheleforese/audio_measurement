from dataclasses import dataclass, field
from pathlib import Path
import rich


@dataclass
@rich.repr.auto
class CacheFile:
    database: dict[str, Path] = field(default_factory=lambda: dict({}))

    def get(self, key: str):
        file = self.database.get(key, None)
        return file

    def add(self, key: str, path: Path) -> bool:
        if self.get(key) is None:
            self.database[key] = path
            return True
        return False


@dataclass
@rich.repr.auto
class File:
    key: str | None = None
    path: str | None = None

    def overload(self, key: str | None, path: str | None):
        if key is not None:
            self.key = key
        if path is not None:
            self.path = path

    def is_null(self) -> bool:
        return self.key is None and self.path is None
