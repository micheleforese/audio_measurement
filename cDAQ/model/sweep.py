from pathlib import Path

import pandas as pd
from pandas import DataFrame, Series
import yaml

from cDAQ.console import console


class SingleSweepData:

    path: Path

    # Meta Information
    frequency: float
    Fs: float

    # CSV Data
    data: DataFrame

    def __init__(self, path: Path) -> None:

        if not path.exists():
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
            [line[2:] for line in self.path.read_text().split("\n") if "#" in line]
        )

        try:
            yaml_dict = yaml.safe_load(data_yaml)
            self.frequency = yaml_dict["frequency"]
            self.Fs = yaml_dict["Fs"]
        except Exception as e:
            console.print(f"Error: {e}")
            exit()

    @property
    def voltages(self) -> Series:
        return self.data["voltages"]


class SweepData:

    path: Path

    # Meta Information
    # TODO: Add Meta Information
    amplitude: float

    # CSV Data
    data: DataFrame

    def __init__(self, path: Path) -> None:
        if not path.exists():
            raise Exception

        self.path = path

        self._load_yaml_comments()

        self.data = pd.read_csv(
            self.path.absolute().resolve(),
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

    def _load_yaml_comments(self):
        data_yaml = "\n".join(
            [line[2:] for line in self.path.read_text().split("\n") if "#" in line]
        )

        try:
            yaml_dict = yaml.safe_load(data_yaml)

            self.amplitude = yaml_dict["amplitude"]

        except Exception as e:
            console.print(f"Error: {e}")
            exit()

    @property
    def frequency(self) -> Series:
        return self.data["frequency"]

    @property
    def rms(self) -> Series:
        return self.data["rms"]

    @property
    def dBV(self) -> Series:
        return self.data["dBV"]

    @property
    def Fs(self) -> Series:
        return self.data["Fs"]

    @property
    def oversampling_ratio(self) -> Series:
        return self.data["oversampling_ratio"]

    @property
    def n_periods(self) -> Series:
        return self.data["n_periods"]

    @property
    def n_samples(self) -> Series:
        return self.data["n_samples"]
