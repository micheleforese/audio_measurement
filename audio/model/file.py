from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional
import rich


@dataclass
@rich.repr.auto
class CacheFile:
    database: Dict[str, Path] = field(default_factory=lambda: dict({}))

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
    key: Optional[str] = None
    path: Optional[str] = None

    def overload(self, key: Optional[str], path: Optional[str]):
        if key is not None:
            self.key = key
        if path is not None:
            self.path = path
