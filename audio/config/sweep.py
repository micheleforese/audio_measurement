from __future__ import annotations

import pathlib
from typing import Dict, Optional

import rich

import audio.config as cfg
from audio.config.nidaq import NiDaq
from audio.config.plot import Plot
from audio.config.rigol import Rigol, RigolConfig
from audio.config.sampling import Sampling
from audio.console import console
from audio.type import Dictionary, Option


@rich.repr.auto
class SweepConfig:

    _config: Dict

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

    @classmethod
    def from_dict(cls, config: cfg.Config_Dict):

        if config is not None:
            # Rigol Class
            rigol = Rigol.from_config(config)

            # NiDaq Class
            nidaq = NiDaq.from_config(config)

            # Sampling Class
            sampling = Sampling.from_config(config)

            # Plot Class
            plot = Plot.from_config(config)

            return cls(rigol, nidaq, sampling, plot)
        else:
            return None

    @property
    def rigol(self) -> Optional[Rigol]:
        return self._rigol

    @rigol.setter
    def rigol(self, value: Rigol):
        self._rigol = value

    @property
    def nidaq(self) -> Optional[NiDaq]:
        return self._nidaq

    @nidaq.setter
    def nidaq(self, value: NiDaq):
        self._nidaq = value

    @property
    def sampling(self) -> Optional[Sampling]:
        return self._sampling

    @sampling.setter
    def sampling(self, value: Sampling):
        self._sampling = value

    @property
    def plot(self) -> Optional[Plot]:
        return self._plot

    @plot.setter
    def plot(self, value: Plot):

        self._plot = value


@rich.repr.auto
class SweepConfigDict(Dictionary):
    def __rich_repr__(self):
        if not self.rigol.is_null:
            yield "rigol", self.rigol.value

    @classmethod
    def from_file(
        cls,
        config_file_path: pathlib.Path,
    ) -> Option[SweepConfigDict]:

        data = Dictionary.from_json(config_file_path)

        if not data.is_null:
            return Option[SweepConfigDict](cls(data.value))

        return Option[SweepConfigDict].null()

    @property
    def rigol(self) -> Option[RigolConfig]:

        rigol = self.get_property("rigol", RigolConfig)

        if not rigol.is_null:
            return Option[RigolConfig](RigolConfig(rigol.value))
        return Option[RigolConfig].null()

    @property
    def nidaq(self) -> Option[RigolConfig]:

        nidaq = self.get_property("nidaq", RigolConfig)

        if not nidaq.is_null:
            return Option[RigolConfig](RigolConfig(nidaq.value))
        return Option[RigolConfig].null()

    @property
    def sampling(self) -> Option[RigolConfig]:

        sampling = self.get_property("sampling", RigolConfig)

        if not sampling.is_null:
            return Option[RigolConfig](RigolConfig(sampling.value))
        return Option[RigolConfig].null()

    @property
    def plot(self) -> Option[RigolConfig]:

        plot = self.get_property("plot", RigolConfig)

        if not plot.is_null:
            return Option[RigolConfig](RigolConfig(plot.value))
        return Option[RigolConfig].null()
