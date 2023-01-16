import os
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection

import numpy as np
import pandas as pd
import xarray as xr

from audio.config.sampling import SamplingConfig
from audio.console import console
from audio.database.db import Database
from audio.math.algorithm import LogarithmicScale
from audio.math.rms import RMS
from audio.model.sampling import VoltageSampling
from audio.utility.timer import Timer


def test_database():

    db = Database()
    db.create_database()

    test_id = db.insert_test("Test 1", datetime.now(), comment="Test di esempio")
    console.log(test_id)

    data = db.get_test(test_id)
    console.log(data)

    return

    # SWEEP
    sweep_id = db.insert_sweep(
        test_id, "Sweep bello", datetime.now(), comment="Uno a caso per prova"
    )
    sweeps = db.get_sweeps()
    console.print(sweeps)

    # CHANNEL
    channel0_id = db.insert_channel(sweep_id, 0, "cDAQ9189-1CDBE0AMod5/ai0")
    channel1_id = db.insert_channel(sweep_id, 1, "cDAQ9189-1CDBE0AMod5/ai1")
    channel2_id = db.insert_channel(sweep_id, 2, "cDAQ9189-1CDBE0AMod5/ai2")
    channels = db.get_channels()
    console.print(channels)

    log_scale: LogarithmicScale = LogarithmicScale(
        min_Hz=20, max_Hz=10000, points_per_decade=10
    )

    Fs_multiplier = 20

    Fs_list = [freq * Fs_multiplier for freq in log_scale.f_list]
    db.insert_frequencies(sweep_id, log_scale.f_list, Fs_list)
    data_frequencies = db.get_frequencies(sweep_id)
    console.print(data_frequencies)

    db.insert_sweep_config(
        sweep_id=sweep_id,
        frequency_min=20,
        frequency_max=10000,
        points_per_decade=10,
        number_of_samples=800,
        Fs_multiplier=Fs_multiplier,
        delay_measurements=None,
        rms=1.78,
        interpolation_rate=20,
    )
    view_sweep = db.view_sweeps()
    console.print(view_sweep)

    def generate_sine_wave(
        freq: float, amplitude: float, sample_rate: float, number_of_sample: int
    ):
        duration = number_of_sample / sample_rate
        time_sampling = 1 / sample_rate
        x = np.arange(
            0.0,
            duration,
            time_sampling,
        )

        # 2pi because np.sin takes radians
        y = amplitude * np.sin((2 * np.pi) * freq * x)
        return (x, y)

    for freq_id, (freq, Fs) in enumerate(zip(log_scale.f_list, Fs_list)):

        freq_id = db.insert_frequency(sweep_id, freq_id, freq, Fs)

        data_x, data_y = generate_sine_wave(freq, 1.5, Fs, 800)
        db.insert_sweep_voltages(
            sweep_id,
            freq_id,
            channel1_id,
            data_y,
        )

    import matplotlib.pyplot as plt

    voltages = db.get_sweep_voltages(sweep_id, channel1_id, 2)
    rms = RMS.rms_v2(
        VoltageSampling.from_list(
            voltages,
            32.2584185780304,
            645.168371560608,
        ),
        trim=True,
    )
    console.log(rms)
    plt.plot(voltages)
    plt.show()
