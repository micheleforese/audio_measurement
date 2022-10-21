from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class CacheFile:
    _database: Dict[str, Path] = dict()

    def get(self, key: str):
        file = self._database.get(key, None)
        return file

    def add(self, key: str, path: Path) -> bool:
        if self.get(key) is None:
            self._database[key] = path
            return True
        return False


@dataclass
class File:
    key: Optional[str]
    path: Optional[Path]

    def overload(self, key: Optional[str], path: Optional[Path]):
        if key is not None:
            self.key = key
        if path is not None:
            self.path = path
