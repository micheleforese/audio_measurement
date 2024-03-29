from __future__ import annotations

import sys
import typing
from typing import Any, Self

import pandas as pd
import yaml
from pandas import DataFrame

from audio.config.plot import PlotConfig
from audio.console import console

if typing.TYPE_CHECKING:
    from pathlib import Path


class SingleSweepData:
    path: Path

    # Meta Information
    frequency: float | None
    Fs: float | None

    # CSV Data
    data: DataFrame

    def __init__(self: SingleSweepData, path: Path) -> None:
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
            sys.exit()

    def _yaml_extract_from_comments(self: Self, data: str) -> dict:
        data_yaml: str = "\n".join(
            [line[2:] for line in data.split("\n") if line.find("#") == 0],
        )
        return dict(yaml.safe_load(data_yaml))

    def _load_yaml_comments(self: Self) -> None:
        yaml_dict = self._yaml_extract_from_comments(self.path.read_text())

        self.frequency = self.get_frequency_from_dictionary(yaml_dict)
        self.Fs = self.get_Fs_from_dictionary(yaml_dict)

    def _meta_info(self: Self, name: str, value: Any) -> str:
        return f"# {name}: {value}\n"

    @staticmethod
    def get_frequency_from_dictionary(dictionary: dict) -> float | None:
        frequency: float | None = dictionary.get("frequency")

        if frequency is not None:
            frequency = float(frequency)

        return frequency

    @staticmethod
    def get_Fs_from_dictionary(dictionary: dict) -> float | None:
        Fs: float | None = dictionary.get("Fs")

        if Fs is not None:
            Fs = float(Fs)

        return Fs

    @property
    def voltages(self: Self):
        return self.data["voltages"]


class SweepData:
    path: Path

    # Meta Information
    amplitude: float | None
    config: PlotConfig | None

    # CSV Data
    data: DataFrame

    def __init__(
        self: SweepData,
        data: DataFrame,
        amplitude: float | None = None,
        config: PlotConfig | None = None,
    ) -> None:
        self.data = data
        self.amplitude = amplitude
        self.config = config

    @classmethod
    def from_csv_file(cls: type[Self], path: Path) -> Self:
        if not path.exists() or not path.is_file():
            raise Exception

        data: DataFrame = pd.read_csv(
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

        amplitude: float | None = SweepData.get_amplitude_from_dictionary(yaml_dict)
        # TODO: Implement PlotConfig.from_dict() version to PlotConfigXML. from_dict()
        plotConfigXML: PlotConfig = PlotConfig()

        return cls(data, amplitude, plotConfigXML)

    def save(self: Self, path: Path) -> None:
        with Path.open(path, "w", encoding="utf-8") as file:
            file.write(
                self._meta_info(
                    "amplitude",
                    round(self.amplitude if self.amplitude is not None else 0, 5),
                ),
            )
            if self.config is not None:
                config_yaml: str = self.config.to_yaml_string()
                yaml_str: str = self._yaml_string_to_yaml_comment(config_yaml)
                console.print(yaml_str)
                file.write(yaml_str)

            self.data.to_csv(
                file,
                header=True,
                index=False,
            )

    @staticmethod
    def _yaml_extract_from_comments(data: str) -> dict:
        data_yaml: str = "\n".join(
            [line[2:] for line in data.splitlines() if line.find("#") == 0],
        )
        return dict(yaml.safe_load(data_yaml))

    def _meta_info(self: Self, name: str, value: Any) -> str:
        return f"# {name}: {value}\n"

    def _yaml_string_to_yaml_comment(self: Self, yaml_string: str) -> str:
        return "\n".join([f"# {line}" for line in yaml_string.splitlines()]) + "\n"

    @staticmethod
    def get_amplitude_from_dictionary(dictionary: dict) -> float | None:
        amplitude: float | None = dictionary.get("amplitude")

        if amplitude is not None:
            amplitude = float(amplitude)

        return amplitude

    @property
    def frequency(self: Self):
        return self.data.get("frequency")

    @property
    def rms(self: Self):
        return self.data.get("rms")

    @property
    def dBV(self: Self):
        return self.data.get("dBV")

    @property
    def Fs(self: Self):
        return self.data.get("Fs")

    @property
    def oversampling_ratio(self: Self):
        return self.data.get("oversampling_ratio")

    @property
    def n_periods(self: Self):
        return self.data.get("n_periods")

    @property
    def n_samples(self: Self):
        return self.data.get("n_samples")
