import pathlib
from typing import Optional

import rich

import audio.config as cfg
from audio.config.nidaq import NiDaq
from audio.config.plot import Plot
from audio.config.rigol import Rigol
from audio.config.sampling import Sampling


@rich.repr.auto
class SweepConfig:

    _rigol: Optional[Rigol]
    _nidaq: Optional[NiDaq]
    _sampling: Optional[Sampling]
    _plot: Optional[Plot]

    def __init__(
        self,
        rigol: Optional[Rigol] = None,
        nidaq: Optional[NiDaq] = None,
        sampling: Optional[Sampling] = None,
        plot: Optional[Plot] = None,
    ) -> None:
        self._rigol = rigol
        self._nidaq = nidaq
        self._sampling = sampling
        self._plot = plot

    @classmethod
    def from_file(cls, config_file_path: pathlib.Path):
        data = cfg.Config_Dict.from_json(config_file_path)

        if data is not None:
            # Rigol Class
            rigol = Rigol.from_config(data)

            # NiDaq Class
            nidaq = NiDaq.from_config(data)

            # Sampling Class
            sampling = Sampling.from_config(data)

            # Plot Class
            plot = Plot.from_config(data)

            return cls(rigol, nidaq, sampling, plot)
        else:
            return None

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
