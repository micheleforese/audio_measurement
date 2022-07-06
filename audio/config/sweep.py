import pathlib
from typing import Optional
import audio.config as cfg

from audio.config.rigol import Rigol
from audio.config.nidaq import NiDaq
from audio.config.sampling import Sampling
from audio.config.plot import Plot


class SweepConfig:

    _rigol: Optional[Rigol]
    _nidaq: Optional[NiDaq]
    _sampling: Optional[Sampling]
    _plot: Optional[Plot]

    def __init__(self) -> None:
        self._rigol = None
        self._nidaq = None
        self._sampling = None
        self._plot = None

    def from_file(self, config_file_path: pathlib.Path):
        self._init_config_from_file(
            cfg.Config_Dict(cfg.load_json_config(config_file_path))
        )

    def _init_config_from_file(self, data: cfg.Config_Dict):

        # Rigol Class
        self._rigol = Rigol(data)

        # NiDaq Class
        self._nidaq = NiDaq(data)

        # Sampling Class
        self._sampling = Sampling(data)

        # Plot Class
        self._plot = Plot(data)

    @property
    def rigol(self):
        return self._rigol

    @rigol.setter
    def rigol(self, value: Rigol):
        self._rigol = value

    @property
    def nidaq(self):
        return self._nidaq

    @nidaq.setter
    def nidaq(self, value: NiDaq):
        self._nidaq = value

    @property
    def sampling(self):
        return self._sampling

    @sampling.setter
    def sampling(self, value: Sampling):
        self._sampling = value

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, value: Plot):

        self._plot = value
