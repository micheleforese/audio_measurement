from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import yaml
from pandas import DataFrame, Series

from audio.console import console


class SingleSweepData:

    path: Path

    # Meta Information
    frequency: Optional[float]
    Fs: Optional[float]

    # CSV Data
    data: DataFrame

    def __init__(self, path: Path) -> None:

        if not path.exists() or not path.is_file():
            raise Exception

        self.path = path

        self._load_yaml_comments()

        try:
            self.data = pd.read_csv(
                self.path.absolute().resolve(),
                header=0,
                comment="#",
                names=["voltages"],
            )
        except Exception as e:
            console.print(f"Error: {e}")
            raise e

    def _load_yaml_comments(self):
        data_yaml = "\n".join(
            [
                line[2:]
                for line in self.path.read_text().split("\n")
                if line.find("#") == 0
            ]
        )

        try:
            yaml_dict: Dict = dict(yaml.safe_load(data_yaml))

            self.frequency = yaml_dict.get("frequency", None)
            self.Fs = yaml_dict.get("Fs", None)

        except Exception as e:
            console.print(f"Error: {e}")
            exit()

    def _meta_info(self, name: str, value: Any):
        return f"# {name}: {value}\n"

    @property
    def voltages(self) -> Series:
        return self.data["voltages"]


class SweepData:

    path: Path

    # Meta Information
    amplitude: Optional[float]
    color: Optional[str]

    # CSV Data
    data: DataFrame

    def __init__(
        self,
        data: DataFrame,
        amplitude: Optional[float],
        color: Optional[str],
    ) -> None:
        self.data = data
        self.amplitude = amplitude
        self.color = color

    @classmethod
    def from_csv_file(cls, path: Path):
        if not path.exists() or not path.is_file():
            raise Exception

        data = pd.read_csv(
            path,
            header=0,
            comment="#",
            names=[
                "frequency",
                "rms",
                "dBV",
                "Fs",
                "oversampling_ratio",
                "n_periods",
                "n_samples",
            ],
        )

        data_yaml = "\n".join(
            [line[2:] for line in path.read_text().split("\n") if line.find("#") == 0]
        )

        yaml_dict: Dict = dict(yaml.safe_load(data_yaml))

        amplitude = yaml_dict.get("amplitude", None)
        color = yaml_dict.get("color", None)

        return cls(data, amplitude, color)

    def save(self, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            if self.amplitude is not None:
                f.write(self._meta_info("amplitude", round(self.amplitude, 5)))
            if self.color is not None:
                f.write(self._meta_info("amplitude", self.color))
            self.data.to_csv(
                f,
                header=True,
                index=None,
            )

    def _meta_info(self, name: str, value: Any):
        return f"# {name}: {value}\n"

    @property
    def frequency(self) -> Series:
        return self.data.get(["frequency"])

    @property
    def rms(self) -> Series:
        return self.data.get(["rms"])

    @property
    def dBV(self) -> Series:
        return self.data.get(["dBV"])

    @property
    def Fs(self) -> Series:
        return self.data.get(["Fs"])

    @property
    def oversampling_ratio(self) -> Series:
        return self.data.get(["oversampling_ratio"])

    @property
    def n_periods(self) -> Series:
        return self.data.get(["n_periods"])

    @property
    def n_samples(self) -> Series:
        return self.data.get(["n_samples"])
