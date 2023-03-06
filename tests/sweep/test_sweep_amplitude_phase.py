from pathlib import Path

from audio.config.nidaq import NiDaqConfig
from audio.config.plot import PlotConfig
from audio.config.rigol import RigolConfig
from audio.config.sampling import SamplingConfig
from audio.config.sweep import SweepConfig


def test_sweep_amplitude_phase():
    Path(__file__).parent
    SweepConfig(
        rigol=RigolConfig(),
        nidaq=NiDaqConfig(),
        sampling=SamplingConfig(),
        plot=PlotConfig(),
    )

    # sweep_amplitude_phase(
    #     config,
    #     sweep_home_path=HOME / "sweep",
    # )
