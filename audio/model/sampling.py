from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd
from pandas import DataFrame
from audio.console import console


@dataclass
class VoltageSampling:
    data: Optional[DataFrame]
    input_frequency: float
    sampling_frequency: float
    amplitude_peak_to_peak: Optional[float] = None

    @classmethod
    def from_list(
        cls,
        voltages: List[float],
        input_frequency: float,
        sampling_frequency: float,
    ):
        return cls(
            DataFrame(voltages, columns=["voltage"]),
            input_frequency,
            sampling_frequency,
        )

    def save(self, file: Path) -> bool:
        if self.data is None:
            return False

        try:
            with open(file, mode="w", encoding="utf-8") as f:
                f.write(f"# frequency: {self.input_frequency:.5}")
                f.write(f"# Fs: {self.sampling_frequency:.5}")
                self.data.to_csv(f, header=["voltage"])
                return True
        except Exception as e:
            console.log(f"{e}")
            return False

    @property
    def voltages(self):
        return self.data["voltage"]
