from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Self

import pandas as pd
from pandas import DataFrame

from audio.console import console
from audio.math.interpolation import INTERPOLATION_KIND, interpolation_model


@dataclass
class VoltageSampling:
    data: DataFrame | None
    input_frequency: float
    sampling_frequency: float
    amplitude_peak_to_peak: float | None = None

    @classmethod
    def from_list(
        cls: type[Self],
        voltages: list[float],
        input_frequency: float,
        sampling_frequency: float,
    ) -> Self:
        return cls(
            DataFrame(voltages, columns=["voltage"]),
            input_frequency,
            sampling_frequency,
        )

    def save(self: Self, file: Path) -> bool:
        if self.data is None:
            return False

        try:
            with Path.open(file, mode="w", encoding="utf-8") as f:
                f.write(f"# frequency: {self.input_frequency:.5}")
                f.write(f"# Fs: {self.sampling_frequency:.5}")
                self.data.to_csv(f, header=["voltage"])
                return True
        except Exception as e:
            console.log(f"{e}")
            return False

    @property
    def voltages(self: Self):
        return self.data["voltage"]


@dataclass
class VoltageSamplingV2:
    data: DataFrame | None
    input_frequency: float
    sampling_frequency: float

    @staticmethod
    def _from_list_to_dataframe(
        voltages: list[float],
        sampling_frequency: float,
    ) -> pd.DataFrame:
        time_in_seconds_x: list[float] = [
            n * (1 / sampling_frequency) for n in range(0, len(voltages))
        ]
        return DataFrame(
            zip(time_in_seconds_x, voltages, strict=True),
            columns=["time", "voltage"],
        )

    @classmethod
    def from_list(
        cls: type[VoltageSamplingV2],
        voltages: list[float],
        input_frequency: float,
        sampling_frequency: float,
    ) -> VoltageSamplingV2:
        return cls(
            cls._from_list_to_dataframe(
                voltages=voltages,
                sampling_frequency=sampling_frequency,
            ),
            input_frequency,
            sampling_frequency,
        )

    def augment_interpolation(
        self: Self,
        interpolation_rate: int,
        interpolation_mode: INTERPOLATION_KIND,
    ) -> Self:
        voltages_len: int = len(self.voltages)
        n_points: int = int(voltages_len * interpolation_rate)

        x_interpolated, y_interpolated = interpolation_model(
            self.times,
            self.voltages,
            n_points,
            kind=interpolation_mode,
        )
        sampling_frequency: float = self.sampling_frequency * interpolation_rate

        new_data: DataFrame = DataFrame(
            zip(x_interpolated, y_interpolated, strict=True),
            columns=["time", "voltage"],
        )

        return type[self](
            data=new_data,
            input_frequency=self.input_frequency,
            sampling_frequency=sampling_frequency,
        )

    def save(self: VoltageSamplingV2, file: Path) -> bool:
        if self.data is None:
            return False

        try:
            with Path.open(file, mode="w", encoding="utf-8") as f:
                self.data.to_csv(f, header=["voltage"])
                return True
        except Exception as e:
            console.log(f"{e}")
            return False

    @property
    def voltages(self: Self):
        return self.data["voltage"]

    @property
    def times(self: Self):
        return self.data["time"]
