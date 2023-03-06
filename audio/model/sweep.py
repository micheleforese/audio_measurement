from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from pandas import DataFrame, Series

from audio.config.plot import PlotConfig
from audio.console import console


class SingleSweepData:

    path: Path

    # Meta Information
    frequency: float | None
    Fs: float | None

    # CSV Data
    data: DataFrame

    def __init__(self, path: Path) -> None:

        self.frequency = None
        self.Fs = None

        if not path.exists() or not path.is_file():
            raise Exception

        self.path = path

        self._load_yaml_comments()

        try:
            self.data = pd.read_csv(
                self.path,
                header=0,
                comment="#",
                names=["voltages"],
            )
        except Exception as e:
            console.print(f"Error: {e}")
            exit()

    def _yaml_extract_from_comments(self, data: str) -> dict:
        data_yaml = "\n".join(
            [line[2:] for line in data.split("\n") if line.find("#") == 0]
        )
        return dict(yaml.safe_load(data_yaml))

    def _load_yaml_comments(self):

        yaml_dict = self._yaml_extract_from_comments(self.path.read_text())

        self.frequency = self.get_frequency_from_dictionary(yaml_dict)
        self.Fs = self.get_Fs_from_dictionary(yaml_dict)

    def _meta_info(self, name: str, value: Any):
        return f"# {name}: {value}\n"

    @staticmethod
    def get_frequency_from_dictionary(dictionary: dict) -> float | None:
        frequency: float | None = dictionary.get("frequency", None)

        if frequency is not None:
            frequency = float(frequency)

        return frequency

    @staticmethod
    def get_Fs_from_dictionary(dictionary: dict) -> float | None:
        Fs: float | None = dictionary.get("Fs", None)

        if Fs is not None:
            Fs = float(Fs)

        return Fs

    @property
    def voltages(self) -> Series:
        return self.data["voltages"]


class SweepData:

    path: Path

    # Meta Information
    amplitude: float | None
    config: PlotConfig | None

    # CSV Data
    data: DataFrame

    def __init__(
        self,
        data: DataFrame,
        amplitude: float | None = None,
        config: PlotConfig = None,
    ) -> None:
        self.data = data
        self.amplitude = amplitude
        self.config = config

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

        yaml_dict = SweepData._yaml_extract_from_comments(path.read_text())

        amplitude = SweepData.get_amplitude_from_dictionary(yaml_dict)
        plotConfigXML = PlotConfigXML.from_dict(yaml_dict)

        return cls(data, amplitude, plotConfigXML)

    def save(self, path: Path):
        with open(path, "w", encoding="utf-8") as file:

            file.write(self._meta_info("amplitude", round(self.amplitude, 5)))
            if self.config is not None:
                config_yaml = self.config.to_yaml_string()
                yaml_str = self._yaml_string_to_yaml_comment(config_yaml)
                console.print(yaml_str)
                file.write(yaml_str)

            self.data.to_csv(
                file,
                header=True,
                index=None,
            )

    @staticmethod
    def _yaml_extract_from_comments(data: str) -> dict:
        data_yaml = "\n".join(
            [line[2:] for line in data.splitlines() if line.find("#") == 0]
        )
        return dict(yaml.safe_load(data_yaml))

    def _meta_info(self, name: str, value: Any):
        return f"# {name}: {value}\n"

    def _yaml_string_to_yaml_comment(self, yaml_string: str):
        return "\n".join([f"# {line}" for line in yaml_string.splitlines()]) + "\n"

    @staticmethod
    def get_amplitude_from_dictionary(dictionary: dict) -> float | None:
        amplitude: float | None = dictionary.get("amplitude", None)

        if amplitude is not None:
            amplitude = float(amplitude)

        return amplitude

    @property
    def frequency(self) -> Series:
        return self.data.get("frequency")

    @property
    def rms(self) -> Series:
        return self.data.get("rms")

    @property
    def dBV(self) -> Series:
        return self.data.get("dBV")

    @property
    def Fs(self) -> Series:
        return self.data.get("Fs")

    @property
    def oversampling_ratio(self) -> Series:
        return self.data.get("oversampling_ratio")

    @property
    def n_periods(self) -> Series:
        return self.data.get("n_periods")

    @property
    def n_samples(self) -> Series:
        return self.data.get("n_samples")
