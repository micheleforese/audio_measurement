from dataclasses import dataclass
from datetime import datetime
from typing import List

import matplotlib.pyplot as plt

from audio.config.nidaq import Channel, NiDaqConfig
from audio.config.plot import PlotConfig
from audio.config.rigol import RigolConfig
from audio.config.sampling import SamplingConfig
from audio.config.sweep import SweepConfig
from audio.console import console
from audio.database.db import Database, DbChannel, DbFrequency, DbSweepVoltage, DbTest
from audio.math.rms import RMS, RMSResult
from audio.model.sampling import VoltageSampling
from audio.sampling import DataSetLevel, config_set_level_v2
from audio.sweep import sweep


def test_v2_procedure():

    db = Database()
    test_id = db.insert_test(
        "Test Machine 1",
        datetime.now(),
        comment="Test Procedure with Database",
    )
    sampling_config = SweepConfig(
        RigolConfig(),
        NiDaqConfig(
            Fs_max=1_000_000,
            channels=["cDAQ9189-1CDBE0AMod5/ai3"],
        ),
        SamplingConfig(Fs_multiplier=50, number_of_samples=200),
        PlotConfig(),
    )
    dBu: float = -2
    data_set_level: DataSetLevel = config_set_level_v2(
        dBu=dBu,
        config=sampling_config,
    )

    console.log(data_set_level)

    config = SweepConfig(
        RigolConfig(amplitude_peak_to_peak=data_set_level.volts),
        NiDaqConfig(
            Fs_max=1_000_000,
            channels=[
                Channel("cDAQ9189-1CDBE0AMod5/ai1", "Ref"),
                Channel("cDAQ9189-1CDBE0AMod5/ai3", "DUT"),
            ],
        ),
        SamplingConfig(
            Fs_multiplier=20,
            points_per_decade=20,
            number_of_samples=200,
            number_of_samples_max=1_000,
            frequency_min=20,
            frequency_max=99_999,
            interpolation_rate=20,
            delay_measurements=0,
        ),
        PlotConfig(),
    )
    sweep_id = sweep(test_id=test_id, config=config)
    console.log(f"[DATA]: sweep_id: {sweep_id}")


def test_calculation():
    db = Database()
    sweep_id = 7

    frequencies: List[DbFrequency] = db.get_frequencies_from_sweep_id(sweep_id=sweep_id)

    channels: List[DbChannel] = db.get_channels_from_sweep_id(sweep_id=sweep_id)

    voltages_ref: List[DbSweepVoltage] = []
    voltages_dut: List[DbSweepVoltage] = []

    for freq in frequencies:
        voltages_ref.append(db.get_sweep_voltages(freq.id, channels[0].id))

    for freq in frequencies:
        voltages_dut.append(db.get_sweep_voltages(freq.id, channels[1].id))

    freq_volts_ref = zip(frequencies, voltages_ref)

    rms_ref: List[RMSResult] = []

    for freq, volt_ref in freq_volts_ref:
        voltage_sampling = VoltageSampling.from_list(
            volt_ref.voltages,
            input_frequency=freq.frequency,
            sampling_frequency=freq.Fs,
        )
        rms = RMS.rms_v2(voltage_sampling, interpolation_rate=20)
        rms_ref.append(rms)

    for freq, rms_result in zip(frequencies, rms_ref):
        console.log(f"[DATA]: freq: {freq.frequency:.05f}, rms: {rms_result.rms:.05f}")

    plt.semilogx(
        [freq.frequency for freq in frequencies],
        [rms.rms for rms in rms_ref],
    )

    plt.show()
