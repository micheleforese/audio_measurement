import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from rich.panel import Panel

from audio.config.nidaq import Channel, NiDaqConfig
from audio.config.plot import PlotConfig
from audio.config.rigol import RigolConfig
from audio.config.sampling import SamplingConfig
from audio.config.sweep import SweepConfig
from audio.console import console
from audio.database.db import Database, DbChannel, DbFrequency, DbSweepVoltage, DbTest
from audio.math.interpolation import INTERPOLATION_KIND, interpolation_model
from audio.math.phase import phase_offset_v2
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
            channels=[
                Channel("cDAQ9189-1CDBE0AMod5/ai1", "Ref"),
                Channel("cDAQ9189-1CDBE0AMod5/ai3", "DUT"),
            ],
        ),
        SamplingConfig(Fs_multiplier=50, number_of_samples=200),
        PlotConfig(),
    )
    dBu: float = -6
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
            Fs_multiplier=50,
            points_per_decade=20,
            number_of_samples=200,
            number_of_samples_max=1_000,
            frequency_min=10,
            frequency_max=300_000,
            interpolation_rate=20,
            delay_measurements=0,
        ),
        PlotConfig(),
    )
    sweep_id = sweep(test_id=test_id, config=config)
    console.log(f"[DATA]: sweep_id: {sweep_id}")

    make_calculation(sweep_id, data_set_level.dB)


def make_calculation(sweep_id: int, dB_offset: float = 0):
    db = Database()

    console.print(Panel("[bold]RETRIEVING DATA FROM DB[/]"))

    frequencies: List[DbFrequency] = db.get_frequencies_from_sweep_id(sweep_id=sweep_id)

    channels: List[DbChannel] = db.get_channels_from_sweep_id(sweep_id=sweep_id)

    voltages_ref: List[DbSweepVoltage] = []
    voltages_dut: List[DbSweepVoltage] = []

    for freq_ref in frequencies:
        voltages_ref.append(db.get_sweep_voltages(freq_ref.id, channels[0].id))

    for freq_ref in frequencies:
        voltages_dut.append(db.get_sweep_voltages(freq_ref.id, channels[1].id))
    make_graph_dB_phase(
        sweep_id=sweep_id,
        frequencies=frequencies,
        voltages_ref=voltages_ref,
        voltages_dut=voltages_dut,
        dB_offset=dB_offset,
    )


def make_graph_ref_dut_dutrefsub_dB_phase(
    sweep_id: int,
    frequencies: List[DbFrequency],
    voltages_ref: List[DbSweepVoltage],
    voltages_dut: List[DbSweepVoltage],
    dB_offset: float = 0,
):
    from audio.constant import APP_HOME

    directory = Path(APP_HOME / "data/imgs")
    directory.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(3, 2)
    figure.set_size_inches(15, 9)
    from rich.prompt import Prompt

    comment = Prompt.ask("Test condition")
    plt.suptitle(f"ID: {sweep_id}, dB: {dB_offset:0.5f}, comment: {comment}")
    # plt.style.use("ggplot")
    plt.style.use("seaborn")

    freq_volts_ref = zip(frequencies, voltages_ref)

    rms_ref: List[RMSResult] = []

    for freq_ref, volt_ref in freq_volts_ref:
        voltage_sampling = VoltageSampling.from_list(
            volt_ref.voltages,
            input_frequency=freq_ref.frequency,
            sampling_frequency=freq_ref.Fs,
        )
        rms = RMS.rms_v2(voltage_sampling, interpolation_rate=50)
        rms_ref.append(rms)

    for freq_ref, rms_result in zip(frequencies, rms_ref):
        console.log(
            f"[DATA]: freq: {freq_ref.frequency:.05f}, rms: {rms_result.rms:.05f}"
        )

    from matplotlib.axes import Axes

    axis_ref: Axes = axis[0, 0]

    axis_ref.semilogx(
        [freq.frequency for freq in frequencies],
        [rms.rms for rms in rms_ref],
    )
    axis_ref.set_title("Ref")

    file = directory / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')}.jpeg"

    # DUT
    freq_volts_dut = zip(frequencies, voltages_dut)

    rms_dut: List[RMSResult] = []

    for freq_ref, volt_dut in freq_volts_dut:
        voltage_sampling = VoltageSampling.from_list(
            volt_dut.voltages,
            input_frequency=freq_ref.frequency,
            sampling_frequency=freq_ref.Fs,
        )
        rms = RMS.rms_v2(voltage_sampling, interpolation_rate=50)
        rms_dut.append(rms)

    for freq_ref, rms_result in zip(frequencies, rms_dut):
        console.log(
            f"[DATA]: freq: {freq_ref.frequency:.05f}, rms: {rms_result.rms:.05f}"
        )

    axis_dut: Axes = axis[0, 1]

    axis_dut.semilogx(
        [freq.frequency for freq in frequencies],
        [rms.rms for rms in rms_dut],
    )
    axis_dut.set_title("DUT")

    file = directory / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')}.jpeg"

    # DUT - Red [VRms]
    axis_dut_sub_ref: Axes = axis[1, 0]

    rms_dut_sub_ref: List[float] = []

    for ref, dut in zip(rms_ref, rms_dut):
        rms_dut_sub_ref.append(dut.rms - ref.rms)

    axis_dut_sub_ref.semilogx(
        [freq.frequency for freq in frequencies],
        rms_dut_sub_ref,
    )
    axis_dut_sub_ref.set_title("DUT - Ref [VRms]")

    # DUT - Red [dB]
    axis_dut_sub_ref_dB: Axes = axis[1, 1]

    rms_dut_sub_ref_dB: List[float] = []

    for ref, dut in zip(rms_ref, rms_dut):
        rms_dut_sub_ref_dB.append(20 * math.log10(dut.rms / ref.rms))

    rms_dut_sub_ref_dB = [rms - dB_offset for rms in rms_dut_sub_ref_dB]

    axis_dut_sub_ref_dB.semilogx(
        [freq.frequency for freq in frequencies],
        rms_dut_sub_ref_dB,
    )
    axis_dut_sub_ref_dB.set_title("DUT - Ref [dB]")
    import numpy as np

    granularity = 0.1
    rms_dut_sub_ref_dB_min = min(rms_dut_sub_ref_dB)
    rms_dut_sub_ref_dB_max = max(rms_dut_sub_ref_dB)

    if abs(rms_dut_sub_ref_dB_min - rms_dut_sub_ref_dB_max) < granularity * 10:
        axis_dut_sub_ref_dB.set_yticks(
            np.arange(
                rms_dut_sub_ref_dB_min - granularity,
                rms_dut_sub_ref_dB_max + granularity,
                granularity,
            )
        )
    axis_dut_sub_ref_dB.grid()

    # DUT - Red [Phase °]
    axis_dut_sub_ref_phase: Axes = axis[2, 0]
    offset_phase_ref_dut: List[float] = []
    interpolation_rate_phase = 50

    for freq, volts_ref, volts_dut in zip(frequencies, voltages_dut, voltages_ref):

        _, y_interpolated_ref = interpolation_model(
            range(0, len(volts_ref.voltages)),
            volts_ref.voltages,
            int(len(volts_ref.voltages) * interpolation_rate_phase),
            kind=INTERPOLATION_KIND.CUBIC,
        )
        voltage_sampling_ref = VoltageSampling.from_list(
            y_interpolated_ref,
            input_frequency=freq.frequency,
            sampling_frequency=freq.Fs * interpolation_rate_phase,
        )
        _, y_interpolated_dut = interpolation_model(
            range(0, len(volts_dut.voltages)),
            volts_dut.voltages,
            int(len(volts_dut.voltages) * interpolation_rate_phase),
            kind=INTERPOLATION_KIND.CUBIC,
        )
        voltage_sampling_dut = VoltageSampling.from_list(
            y_interpolated_dut,
            input_frequency=freq.frequency,
            sampling_frequency=freq.Fs * interpolation_rate_phase,
        )
        offset_phase = phase_offset_v2(voltage_sampling_ref, voltage_sampling_dut)
        console.log(offset_phase)
        offset_phase_ref_dut.append(offset_phase)

    axis_dut_sub_ref_phase.semilogx(
        [freq.frequency for freq in frequencies],
        offset_phase_ref_dut,
    )
    axis_dut_sub_ref_phase.set_yticks(
        np.arange(
            -180,
            180 + 1,
            30,
        )
    )
    axis_dut_sub_ref_phase.grid()
    plt.savefig(file)

    plt.show()
    plt.close()
    print(plt.style.available)


from rich.prompt import Prompt


def make_graph_dB_phase(
    sweep_id: int,
    frequencies: List[DbFrequency],
    voltages_ref: List[DbSweepVoltage],
    voltages_dut: List[DbSweepVoltage],
    dB_offset: float = 0,
):
    from audio.constant import APP_HOME

    directory = Path(APP_HOME / "data/imgs")
    directory.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(2, 1)
    figure.set_size_inches(15, 9)

    comment = Prompt.ask("Test condition")
    plt.suptitle(f"ID: {sweep_id}, dB: {dB_offset:0.5f}, comment: {comment}")
    plt.style.use("seaborn")

    console.print(Panel("[bold]CREATING PLOT[/]"))

    freq_volts_ref = zip(frequencies, voltages_ref)

    rms_ref: List[RMSResult] = []

    # Ref
    for freq_ref, volt_ref in freq_volts_ref:
        voltage_sampling = VoltageSampling.from_list(
            volt_ref.voltages,
            input_frequency=freq_ref.frequency,
            sampling_frequency=freq_ref.Fs,
        )
        rms = RMS.rms_v2(voltage_sampling, interpolation_rate=50)
        rms_ref.append(rms)

    # for freq_ref, rms_result in zip(frequencies, rms_ref):
    #     console.log(
    #         f"[DATA]: freq: {freq_ref.frequency:.05f}, rms: {rms_result.rms:.05f}"
    #     )

    # DUT
    freq_volts_dut = zip(frequencies, voltages_dut)

    rms_dut: List[RMSResult] = []

    for freq_ref, volt_dut in freq_volts_dut:
        voltage_sampling = VoltageSampling.from_list(
            volt_dut.voltages,
            input_frequency=freq_ref.frequency,
            sampling_frequency=freq_ref.Fs,
        )
        rms = RMS.rms_v2(voltage_sampling, interpolation_rate=50)
        rms_dut.append(rms)

    # for freq_ref, rms_result in zip(frequencies, rms_dut):
    #     console.log(
    #         f"[DATA]: freq: {freq_ref.frequency:.05f}, rms: {rms_result.rms:.05f}"
    #     )

    # DUT - Red [dB]
    axis_dut_sub_ref_dB: Axes = axis[0]

    rms_dut_sub_ref_dB: List[float] = []

    for ref, dut in zip(rms_ref, rms_dut):
        rms_dut_sub_ref_dB.append(20 * math.log10(dut.rms / ref.rms))

    rms_dut_sub_ref_dB = [rms - dB_offset for rms in rms_dut_sub_ref_dB]

    axis_dut_sub_ref_dB.semilogx(
        [freq.frequency for freq in frequencies],
        rms_dut_sub_ref_dB,
    )
    axis_dut_sub_ref_dB.set_title("DUT - Ref [dB]")
    import numpy as np

    granularity = 0.1
    rms_dut_sub_ref_dB_min = min(rms_dut_sub_ref_dB)
    rms_dut_sub_ref_dB_max = max(rms_dut_sub_ref_dB)

    if abs(rms_dut_sub_ref_dB_min - rms_dut_sub_ref_dB_max) < granularity * 10:
        axis_dut_sub_ref_dB.set_yticks(
            np.arange(
                rms_dut_sub_ref_dB_min - granularity,
                rms_dut_sub_ref_dB_max + granularity,
                granularity,
            )
        )
    axis_dut_sub_ref_dB.grid()

    # DUT - Red [Phase °]
    axis_dut_sub_ref_phase: Axes = axis[1]
    offset_phase_ref_dut: List[float] = []
    interpolation_rate_phase = 50

    for freq, volts_ref, volts_dut in zip(frequencies, voltages_dut, voltages_ref):

        _, y_interpolated_ref = interpolation_model(
            range(0, len(volts_ref.voltages)),
            volts_ref.voltages,
            int(len(volts_ref.voltages) * interpolation_rate_phase),
            kind=INTERPOLATION_KIND.CUBIC,
        )
        voltage_sampling_ref = VoltageSampling.from_list(
            y_interpolated_ref,
            input_frequency=freq.frequency,
            sampling_frequency=freq.Fs * interpolation_rate_phase,
        )
        _, y_interpolated_dut = interpolation_model(
            range(0, len(volts_dut.voltages)),
            volts_dut.voltages,
            int(len(volts_dut.voltages) * interpolation_rate_phase),
            kind=INTERPOLATION_KIND.CUBIC,
        )
        voltage_sampling_dut = VoltageSampling.from_list(
            y_interpolated_dut,
            input_frequency=freq.frequency,
            sampling_frequency=freq.Fs * interpolation_rate_phase,
        )
        offset_phase = phase_offset_v2(voltage_sampling_ref, voltage_sampling_dut)
        offset_phase_ref_dut.append(offset_phase)

    axis_dut_sub_ref_phase.semilogx(
        [freq.frequency for freq in frequencies],
        offset_phase_ref_dut,
    )
    axis_dut_sub_ref_phase.set_yticks(
        np.arange(
            -180,
            180 + 1,
            15,
        )
    )
    axis_dut_sub_ref_phase.grid()

    file = directory / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')}.jpeg"
    plt.savefig(file)

    plt.show()
    plt.close()


def test_calculation():
    make_calculation(sweep_id=45, dB_offset=10.06194)
