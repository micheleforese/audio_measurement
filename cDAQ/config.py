from typing import Any, List
from sympy import And
from cDAQ.console import console
import jstyleson


def load_json_config(config_file_path):
    with open(config_file_path) as config_file:
        config = jstyleson.loads(config_file.read())
        return config


class Nidaq():
    max_voltage: float
    min_voltage: float
    ch_input: str


class Sampling():
    points_per_decade: int
    min_Hz: float
    max_Hz: float
    amplitude_pp: float


class Config():
    row_data: Any

    number_of_samples: int
    Fs: int
    amplitude_pp: int
    nidaq: Nidaq
    sampling: Sampling

    step: float

    delay_min: float = 0.001
    aperture_min: float = 0.01
    interval_min: float = 0.01

    def __init__(self, config_file_path: str) -> None:
        self.row_data = load_json_config(config_file_path)
        self._init_config()

    def _init_config(self):

        self.number_of_samples = int(self.row_data['number_of_samples'])
        self.Fs = int(self.row_data['Fs'])
        self.amplitude_pp = float(self.row_data['amplitude_pp'])

        self.nidaq.max_voltage = float(self.row_data['nidaq']['max_voltage'])
        self.nidaq.min_voltage = float(self.row_data['nidaq']['min_voltage'])
        self.nidaq.ch_input = float(self.row_data['nidaq']['ch_input'])

        self.sampling.points_per_decade = int(
            self.row_data['sampling']['points_per_decade'])
        self.sampling.min_Hz = float(self.row_data['sampling']['min_Hz'])
        self.sampling.max_Hz = float(self.row_data['sampling']['max_Hz'])
        self.sampling.amplitude_pp = float(
            self.row_data['sampling']['amplitude_pp'])

        # Calculations
        self.step = 1 / self.sampling.points_per_decade
