import json
import math
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import requests
from matplotlib import ticker
from matplotlib.axes import Axes
from rich.panel import Panel
from rich.prompt import Prompt

from audio.config.nidaq import Channel, NiDaqConfig
from audio.config.plot import PlotConfig
from audio.config.rigol import RigolConfig
from audio.config.sampling import SamplingConfig
from audio.config.sweep import SweepConfig
from audio.console import console
from audio.constant import APP_HOME
from audio.database.db import Database, DbChannel, DbFrequency, DbSweepVoltage
from audio.logging import log
from audio.math.interpolation import (
    INTERPOLATION_KIND,
    interpolation_model,
    logx_interpolation_model_smoothing_spline,
)
from audio.math.phase import phase_offset_v2, phase_offset_v4
from audio.math.rms import RMS, RMS_MODE, RMSResult
from audio.math.voltage import calculate_gain_dB
from audio.model.sampling import VoltageSampling, VoltageSamplingV2
from audio.sampling import (
    DataSetLevel,
    config_balanced_set_level_v2,
    config_set_level_v2,
)
from audio.sweep import sweep, sweep_balanced, sweep_balanced_single, sweep_single
from audio.utility.timer import Timer


def test_v2_procedure():
    db = Database()
    test_id = db.insert_test(
        "Test Machine 1",
        datetime.now(),
        comment="Test Procedure with Database",
    )

    PB_test_id: str | None = None
    url = "http://127.0.0.1:8090/api/collections/tests/records"
    response = requests.post(
        url,
        json={
            "name": "Test v2 Procedure",
            "comment": "v2 Procedure Comment",
        },
        timeout=5,
    )
    response_data = json.loads(response.content.decode())
    console.log(response_data)
    if response.status_code != 200:
        console.log(f"[RESPONSE ERROR]: {url}")
    else:
        PB_test_id = response_data["id"]

    channel_ref = Channel("cDAQ9189-1CDBE0AMod5/ai1", "Ref")
    channel_dut = Channel("cDAQ9189-1CDBE0AMod5/ai2", "DUT")

    sampling_config = SweepConfig(
        RigolConfig(),
        NiDaqConfig(
            max_frequency_sampling=1_000_000,
            channels=[channel_ref, channel_dut],
        ),
        SamplingConfig(
            Fs_multiplier=50,
            number_of_samples=500,
        ),
        PlotConfig(),
    )
    dBu: float = -6
    data_set_level: DataSetLevel = config_set_level_v2(
        dBu=dBu,
        config=sampling_config,
    )

    console.log(data_set_level)
    log.info(f"[DATA] dB setlevel {data_set_level}")

    data_set_level.dB = sweep_single(
        data_set_level.volts,
        frequency=1000,
        n_sweep=10,
        config=sampling_config,
    )

    config = SweepConfig(
        RigolConfig(amplitude_peak_to_peak=data_set_level.volts),
        NiDaqConfig(
            max_frequency_sampling=1_000_000,
            channels=[channel_ref, channel_dut],
        ),
        SamplingConfig(
            Fs_multiplier=50,
            points_per_decade=50,
            number_of_samples=200,
            number_of_samples_max=1_000,
            frequency_min=10,
            frequency_max=200_000,
            interpolation_rate=50,
            delay_measurements=0,
        ),
        PlotConfig(),
    )
    sweep_id = sweep(test_id=test_id, PB_test_id=PB_test_id, config=config)
    console.log(f"[DATA]: sweep_id: {sweep_id}")
    log.info(f"[DATA] sweep_id: {sweep_id}")

    make_calculation(sweep_id, data_set_level.dB)


def make_calculation(sweep_id: int, dB_offset: float = 0):
    db = Database()

    console.print(Panel("[bold]RETRIEVING DATA FROM DB[/]"))

    frequencies: list[DbFrequency] = db.get_frequencies_from_sweep_id(sweep_id=sweep_id)

    channels: list[DbChannel] = db.get_channels_from_sweep_id(sweep_id=sweep_id)

    voltages_ref: list[DbSweepVoltage] = []
    voltages_dut: list[DbSweepVoltage] = []

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
    frequencies: list[DbFrequency],
    voltages_ref: list[DbSweepVoltage],
    voltages_dut: list[DbSweepVoltage],
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
    plt.style.use("ggplot")

    freq_volts_ref = zip(frequencies, voltages_ref)

    rms_ref: list[RMSResult] = []

    for freq_ref, volt_ref in freq_volts_ref:
        voltage_sampling = VoltageSampling.from_list(
            volt_ref.voltages,
            input_frequency=freq_ref.frequency,
            sampling_frequency=freq_ref.sampling_frequency,
        )
        rms = RMS.rms_v2(voltage_sampling, interpolation_rate=50)
        rms_ref.append(rms)

    for freq_ref, rms_result in zip(frequencies, rms_ref):
        console.log(
            f"[DATA]: freq: {freq_ref.frequency:.05f}, rms: {rms_result.rms:.05f}",
        )

    axis_ref: Axes = axis[0, 0]

    axis_ref.semilogx(
        [freq.frequency for freq in frequencies],
        [rms.rms for rms in rms_ref],
    )
    axis_ref.set_title("Ref")

    file = directory / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')}.jpeg"

    # DUT
    freq_volts_dut = zip(frequencies, voltages_dut)

    rms_dut: list[RMSResult] = []

    for freq_ref, volt_dut in freq_volts_dut:
        voltage_sampling = VoltageSampling.from_list(
            volt_dut.voltages,
            input_frequency=freq_ref.frequency,
            sampling_frequency=freq_ref.sampling_frequency,
        )
        rms = RMS.rms_v2(voltage_sampling, interpolation_rate=50)
        rms_dut.append(rms)

    for freq_ref, rms_result in zip(frequencies, rms_dut):
        console.log(
            f"[DATA]: freq: {freq_ref.frequency:.05f}, rms: {rms_result.rms:.05f}",
        )

    axis_dut: Axes = axis[0, 1]

    axis_dut.semilogx(
        [freq.frequency for freq in frequencies],
        [rms.rms for rms in rms_dut],
    )
    axis_dut.set_title("DUT")

    file = directory / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')}.jpeg"

    axis_dut_sub_ref: Axes = axis[1, 0]

    rms_dut_sub_ref: list[float] = []

    for ref, dut in zip(rms_ref, rms_dut):
        rms_dut_sub_ref.append(dut.rms - ref.rms)

    axis_dut_sub_ref.semilogx(
        [freq.frequency for freq in frequencies],
        rms_dut_sub_ref,
    )
    axis_dut_sub_ref.set_title("DUT - Ref [VRms]")

    axis_dut_sub_ref_dB: Axes = axis[1, 1]

    rms_dut_sub_ref_dB: list[float] = []

    for ref, dut in zip(rms_ref, rms_dut):
        rms_dut_sub_ref_dB.append(20 * math.log10(dut.rms / ref.rms))

    rms_dut_sub_ref_dB = [rms - dB_offset for rms in rms_dut_sub_ref_dB]

    axis_dut_sub_ref_dB.semilogx(
        [freq.frequency for freq in frequencies],
        rms_dut_sub_ref_dB,
    )
    axis_dut_sub_ref_dB.set_title("DUT - Ref [dB]")

    granularity = 0.1
    rms_dut_sub_ref_dB_min = min(rms_dut_sub_ref_dB)
    rms_dut_sub_ref_dB_max = max(rms_dut_sub_ref_dB)

    if abs(rms_dut_sub_ref_dB_min - rms_dut_sub_ref_dB_max) < granularity * 10:
        axis_dut_sub_ref_dB.set_yticks(
            np.arange(
                rms_dut_sub_ref_dB_min - granularity,
                rms_dut_sub_ref_dB_max + granularity,
                granularity,
            ),
        )
    axis_dut_sub_ref_dB.grid()

    # DUT - Red [Phase °]
    axis_dut_sub_ref_phase: Axes = axis[2, 0]
    offset_phase_ref_dut: list[float] = []
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
            sampling_frequency=freq.sampling_frequency * interpolation_rate_phase,
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
            sampling_frequency=freq.sampling_frequency * interpolation_rate_phase,
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
        ),
    )
    axis_dut_sub_ref_phase.grid()
    plt.savefig(file)

    plt.show()
    plt.close()
    print(plt.style.available)


def make_graph_dB_phase(
    sweep_id: int,
    frequencies: list[DbFrequency],
    voltages_ref: list[DbSweepVoltage],
    voltages_dut: list[DbSweepVoltage],
    dB_offset: float = 0,
):
    log.info("make_graph_dB_phase")

    directory = Path(APP_HOME / "data/imgs")
    directory.mkdir(parents=True, exist_ok=True)

    timer = Timer()

    timer.start()

    figure, axis = plt.subplots(2, 1)
    figure.set_size_inches(15, 9)
    figure.tight_layout(pad=5.0)

    timer_lap = timer.lap()
    log.info(f"TIME INIT PLOT: {timer_lap}")

    comment = Prompt.ask("Test condition", default=None)
    timer_lap = timer.lap()
    plt.suptitle(f"ID: {sweep_id}, dB: {dB_offset:0.5f}, comment: {comment}")
    plt.style.use("seaborn")

    console.print(Panel("[bold]CREATING PLOT[/]"))

    interpolation_rate_rms = 50

    voltage_sampling_ref_list: list[VoltageSamplingV2] = []
    voltage_sampling_dut_list: list[VoltageSamplingV2] = []

    # Ref
    freq_volts_ref = zip(frequencies, voltages_ref)
    rms_ref: list[float] = []
    for freq_ref, volt_ref in freq_volts_ref:
        voltage_sampling = VoltageSamplingV2.from_list(
            volt_ref.voltages,
            input_frequency=freq_ref.frequency,
            sampling_frequency=freq_ref.sampling_frequency,
        )
        voltage_sampling_ref_list.append(voltage_sampling)

        rms = RMS.rms_v3(
            voltage_sampling.augment_interpolation(
                interpolation_rate=interpolation_rate_rms,
                interpolation_mode=INTERPOLATION_KIND.CUBIC,
            ),
            trim=True,
            rms_mode=RMS_MODE.FFT,
        )
        rms_ref.append(rms)

    timer_lap = timer.lap()
    log.info(f"TIME CALCULATION REF RMS: {timer_lap}")

    # DUT
    freq_volts_dut = zip(frequencies, voltages_dut)
    rms_dut: list[RMSResult] = []
    for freq_ref, volt_dut in freq_volts_dut:
        voltage_sampling = VoltageSamplingV2.from_list(
            volt_dut.voltages,
            input_frequency=freq_ref.frequency,
            sampling_frequency=freq_ref.sampling_frequency,
        )
        voltage_sampling_dut_list.append(voltage_sampling)

        rms = RMS.rms_v3(
            voltage_sampling.augment_interpolation(
                interpolation_rate=interpolation_rate_rms,
                interpolation_mode=INTERPOLATION_KIND.CUBIC,
            ),
            trim=True,
            rms_mode=RMS_MODE.FFT,
        )
        rms_dut.append(rms)

    timer_lap = timer.lap()
    log.info(f"TIME CALCULATION DUT RMS: {timer_lap}")

    axis_dut_sub_ref_dB: Axes = axis[0]
    axis_dut_sub_ref_dB.set_title("DUT - Ref [dB]")
    axis_dut_sub_ref_dB.set_xlabel("Frequency")
    axis_dut_sub_ref_dB.set_ylabel("dB")
    axis_dut_sub_ref_dB.tick_params(labelright=True)

    rms_dut_sub_ref_dB: list[float] = [
        calculate_gain_dB(ref, dut) - dB_offset for ref, dut in zip(rms_ref, rms_dut)
    ]

    (
        axis_dut_sub_ref_dB_data_x,
        axis_dut_sub_ref_dB_data_y,
    ) = logx_interpolation_model_smoothing_spline(
        [freq.frequency for freq in frequencies],
        rms_dut_sub_ref_dB,
        1,
        lam=0.00001,
    )

    #     axis_dut_sub_ref_dB_data_x,
    #     axis_dut_sub_ref_dB_data_y,
    # ) = logx_interpolation_model(
    #     rms_dut_sub_ref_dB,

    axis_dut_sub_ref_dB.semilogx(
        [freq.frequency for freq in frequencies],
        rms_dut_sub_ref_dB,
        ".",
        color="blue",
        markersize=3,
    )
    axis_dut_sub_ref_dB.semilogx(
        axis_dut_sub_ref_dB_data_x,
        axis_dut_sub_ref_dB_data_y,
        "-",
        color="red",
        linewidth=1,
    )
    if min(axis_dut_sub_ref_dB_data_y) < -3:
        axis_dut_sub_ref_dB.axhline(0, color="black", linewidth=1)
        axis_dut_sub_ref_dB.axhline(-3, color="green", linewidth=1)

    axis_dut_sub_ref_dB.axes.xaxis.set_minor_formatter(ticker.NullFormatter())
    axis_dut_sub_ref_dB.axes.xaxis.set_major_formatter(ticker.ScalarFormatter())
    axis_dut_sub_ref_dB.grid(which="major", color="grey", linestyle="-")
    axis_dut_sub_ref_dB.grid(which="minor", color="grey", linestyle="--")

    timer_lap = timer.lap()
    log.info(f"TIME DUT - REF dB PLOT: {timer_lap}")

    # DUT - Red [Phase °]
    axis_dut_sub_ref_phase_ax1: Axes = axis[1]
    axis_dut_sub_ref_phase_ax1.set_title("DUT - REF Phase [°]")
    axis_dut_sub_ref_phase_ax1.set_xlabel("Frequency")
    axis_dut_sub_ref_phase_ax1.set_ylabel("Degrees [°]")
    axis_dut_sub_ref_phase_ax1.tick_params(labelright=True)
    axis_dut_sub_ref_phase_ax1.axhline(0, color="black", linewidth=1)

    offset_phase_ref_dut: list[float] = []

    interpolation_rate_phase = 50

    for _freq, volts_ref, volts_dut in zip(
        frequencies,
        voltage_sampling_dut_list,
        voltage_sampling_ref_list,
        strict=True,
    ):
        voltage_sampling_ref = volts_ref.augment_interpolation(
            interpolation_rate=interpolation_rate_phase,
            interpolation_mode=INTERPOLATION_KIND.CUBIC,
        )

        voltage_sampling_dut = volts_dut.augment_interpolation(
            interpolation_rate=interpolation_rate_phase,
            interpolation_mode=INTERPOLATION_KIND.CUBIC,
        )

        try:
            offset_phase = phase_offset_v4(
                voltage_sampling_ref,
                voltage_sampling_dut,
            )
        except Exception as e:
            console.log(f"{e}")

            plt.close()
            plt.plot(voltage_sampling_ref.voltages, ".-", color="blue")
            plt.plot(voltage_sampling_dut.voltages, ".-", color="red")
            plt.show()
            plt.close()

        offset_phase_ref_dut.append(offset_phase)

    # --------------------------------------
    # for idx in range(1, len(sign_phase_list)):

    #     if is_cross:
    #         if (
    #             curr_sign_phase - prev_sign_phase < 0
    #             and abs(offset_phase_ref_dut[idx - 1] - offset_phase_ref_dut[idx]) > 100
    #         ):

    # for index_transform in index_to_transform:

    #     for idx, phase_value in enumerate(offset_phase_ref_dut):
    #         if idx <= index_transform:

    # for idx in range(1, len(sign_phase_list)):

    #     if is_cross:
    #         if (
    #             curr_sign_phase - prev_sign_phase > 0
    #             and abs(offset_phase_ref_dut[idx - 1] - offset_phase_ref_dut[idx]) > 100
    #         ):

    # for index_transform in index_to_transform:

    #     for idx, phase_value in enumerate(offset_phase_ref_dut):
    #         if idx <= index_transform:
    # --------------------------------------

    # TODO: V2
    # for idx in range(1, len(offset_phase_ref_dut)):

    #     if curr_sign_phase - prev_sign_phase:
    #         if (
    #             curr_sign_phase - prev_sign_phase > 0
    #             and abs(offset_phase_ref_dut[idx - 1] - offset_phase_ref_dut[idx]) > 100
    #         ):

    # TODO: V1
    for idx, value in enumerate(offset_phase_ref_dut):
        if value > 180:
            offset_phase_ref_dut[idx] -= 360

    (
        axis_dut_sub_ref_dB_data_x,
        axis_dut_sub_ref_dB_data_y,
    ) = logx_interpolation_model_smoothing_spline(
        [freq.frequency for freq in frequencies],
        offset_phase_ref_dut,
        1,
        lam=0.00001,
    )

    #     axis_dut_sub_ref_dB_data_x,
    #     axis_dut_sub_ref_dB_data_y,
    # ) = logx_interpolation_model(
    #     offset_phase_ref_dut,
    axis_dut_sub_ref_phase_ax1.semilogx(
        [freq.frequency for freq in frequencies],
        offset_phase_ref_dut,
        ".",
        color="blue",
        markersize=3,
    )
    axis_dut_sub_ref_phase_ax1.semilogx(
        axis_dut_sub_ref_dB_data_x,
        axis_dut_sub_ref_dB_data_y,
        "-",
        color="red",
        linewidth=1,
    )

    data_phase_y_max = max(offset_phase_ref_dut)
    data_phase_y_min = min(offset_phase_ref_dut)

    data_phase_y_range_max: int
    data_phase_y_range_min: int

    if data_phase_y_max < 30:
        data_phase_y_range_max = 30
    elif data_phase_y_max < 45:
        data_phase_y_range_max = 45
    elif data_phase_y_max <= 90:
        data_phase_y_range_max = 90
    elif data_phase_y_max <= 180:
        data_phase_y_range_max = 180
    else:
        data_phase_y_range_max = data_phase_y_max

    if data_phase_y_min > -30:
        data_phase_y_range_min = -30
    elif data_phase_y_min > -45:
        data_phase_y_range_min = -45
    elif data_phase_y_min >= -90:
        data_phase_y_range_min = -90
    elif data_phase_y_min >= -180:
        data_phase_y_range_min = -180
    else:
        data_phase_y_range_min = data_phase_y_min

    data_phase_y_total_range = int(data_phase_y_range_max - data_phase_y_range_min)

    data_phase_y_total_range_step: int = 5

    if data_phase_y_total_range <= 60:
        data_phase_y_total_range_step = 3
    elif data_phase_y_total_range <= 120:
        data_phase_y_total_range_step = 5
    elif data_phase_y_total_range <= 240:
        data_phase_y_total_range_step = 10
    elif data_phase_y_total_range <= 360:
        data_phase_y_total_range_step = 15
    else:
        data_phase_y_total_range_step = int(data_phase_y_total_range % 120) * 5

    axis_dut_sub_ref_phase_ax1.set_yticks(
        np.arange(
            data_phase_y_range_min,
            data_phase_y_range_max + 1,
            data_phase_y_total_range_step,
            dtype=int,
        ),
    )

    axis_dut_sub_ref_phase_ax1.axes.xaxis.set_minor_formatter(ticker.NullFormatter())
    axis_dut_sub_ref_phase_ax1.axes.xaxis.set_major_formatter(ticker.ScalarFormatter())
    axis_dut_sub_ref_phase_ax1.grid(which="major", color="grey", linestyle="-")
    axis_dut_sub_ref_phase_ax1.grid(which="minor", color="grey", linestyle="--")

    timer_lap = timer.lap()
    log.info(f"TIME DUT - REF PHASE PLOT: {timer_lap}")

    elapsed_time = timer.stop()
    log.info(f"TIME TOTAL: {elapsed_time}")

    file = directory / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')}.jpeg"
    plt.savefig(file)

    with open(file, mode="rb") as f:
        response = requests.post(
            "http://127.0.0.1:8090/api/collections/graphs/records",
            data={
                "sweep_id": sweep_id,
                "gain_dB": dB_offset,
                "comment": comment,
            },
            files={"file": f},
            timeout=5,
        )
        if response.status_code != 200:
            data = json.loads(response.content)
            console.log(data)

    plt.show()
    plt.close()


def parallel_calculate_rms(data: list[tuple[DbFrequency, DbSweepVoltage]]):
    from multiprocessing.pool import Pool

    data: list[tuple[int, tuple[DbFrequency, DbSweepVoltage]]] = [
        (idx, d) for idx, d in enumerate(data)
    ]

    rms_list: list[tuple[int, RMSResult]] = []

    with Pool() as pool:
        results = pool.imap_unordered(parallel_calculate_rms_calulate, data)
        for result in results:
            rms_list.append(result)

    rms_list.sort(key=lambda x: x[0])
    rms_list = [rms for idx, rms in rms_list]
    return rms_list


def parallel_calculate_rms_calulate(
    data: tuple[int, tuple[DbFrequency, DbSweepVoltage]],
):
    idx, data_db = data
    freq, volt = data_db

    voltage_sampling = VoltageSampling.from_list(
        volt.voltages,
        input_frequency=freq.frequency,
        sampling_frequency=freq.sampling_frequency,
    )
    rms = RMS.rms_v2(
        voltage_sampling,
        interpolation_rate=50,
        trim=True,
    )

    return (idx, rms)


def test_calculation():
    make_calculation(
        sweep_id=233,
        dB_offset=1.41326,
    )


def test_v2_balanced_procedure():
    db = Database()
    test_id = db.insert_test(
        "Test Machine 1",
        datetime.now(),
        comment="Test Procedure with Database",
    )

    PB_test_id: str | None = None
    url = "http://127.0.0.1:8090/api/collections/tests/records"
    response = requests.post(
        url,
        json={
            "name": "Test v2 Procedure",
            "comment": "v2 Procedure Comment",
        },
        timeout=5,
    )
    response_data = json.loads(response.content.decode())
    console.log(response_data)
    if response.status_code != 200:
        console.log(f"[RESPONSE ERROR]: {url}")
    else:
        PB_test_id = response_data["id"]

    channel_ref_plus = Channel("cDAQ9189-1CDBE0AMod5/ai0", "Ref+")
    channel_ref_minus = Channel("cDAQ9189-1CDBE0AMod5/ai1", "Ref-")
    channel_dut_plus = Channel("cDAQ9189-1CDBE0AMod5/ai2", "DUT+")
    channel_dut_minus = Channel("cDAQ9189-1CDBE0AMod5/ai3", "DUT-")

    sampling_config = SweepConfig(
        RigolConfig(),
        NiDaqConfig(
            max_frequency_sampling=1_000_000,
            channels=[
                channel_ref_plus,
                channel_ref_minus,
                channel_dut_plus,
                channel_dut_minus,
            ],
        ),
        SamplingConfig(
            Fs_multiplier=50,
            number_of_samples=500,
        ),
        PlotConfig(),
    )
    dBu: float = 0
    data_set_level: DataSetLevel = config_balanced_set_level_v2(
        dBu=dBu,
        config=sampling_config,
    )

    console.log(data_set_level)
    log.info(f"[DATA] dB setlevel {data_set_level}")

    data_set_level.dB = sweep_balanced_single(
        data_set_level.volts,
        frequency=1000,
        n_sweep=10,
        config=sampling_config,
    )

    config = SweepConfig(
        RigolConfig(amplitude_peak_to_peak=data_set_level.volts),
        NiDaqConfig(
            max_frequency_sampling=1_000_000,
            channels=[
                channel_ref_plus,
                channel_ref_minus,
                channel_dut_plus,
                channel_dut_minus,
            ],
        ),
        SamplingConfig(
            Fs_multiplier=51,
            points_per_decade=300,
            number_of_samples=200,
            number_of_samples_max=1_000,
            frequency_min=8_000,
            frequency_max=30_000,
            interpolation_rate=50,
            delay_measurements=0,
        ),
        PlotConfig(),
    )
    sweep_id = sweep_balanced(test_id=test_id, PB_test_id=PB_test_id, config=config)
    console.log(f"[DATA]: sweep_id: {sweep_id}")
    log.info(f"[DATA] sweep_id: {sweep_id}")

    make_balanced_calculation(sweep_id, data_set_level.dB)


def make_balanced_calculation(sweep_id: int, dB_offset: float = 0):
    db = Database()

    console.print(Panel("[bold]RETRIEVING DATA FROM DB[/]"))

    frequencies: list[DbFrequency] = db.get_frequencies_from_sweep_id(sweep_id=sweep_id)

    channels: list[DbChannel] = db.get_channels_from_sweep_id(sweep_id=sweep_id)

    voltages_ref_plus: list[VoltageSamplingV2] = []
    voltages_ref_minus: list[VoltageSamplingV2] = []
    voltages_dut_plus: list[VoltageSamplingV2] = []
    voltages_dut_minus: list[VoltageSamplingV2] = []

    voltages_ref: list[VoltageSamplingV2] = []
    voltages_dut: list[VoltageSamplingV2] = []

    for freq in frequencies:
        voltages_ref_plus_raw_db = db.get_sweep_voltages(freq.id, channels[0].id)
        voltages_ref_plus_raw = VoltageSamplingV2.from_list(
            voltages_ref_plus_raw_db.voltages,
            input_frequency=freq.frequency,
            sampling_frequency=freq.sampling_frequency,
        )
        voltages_ref_plus.append(voltages_ref_plus_raw)

        voltages_ref_minus_raw_db = db.get_sweep_voltages(freq.id, channels[1].id)
        voltages_ref_minus_raw = VoltageSamplingV2.from_list(
            voltages_ref_minus_raw_db.voltages,
            input_frequency=freq.frequency,
            sampling_frequency=freq.sampling_frequency,
        )
        voltages_ref_minus.append(voltages_ref_minus_raw)

        voltages_ref_raw: list[float] = []
        for plus, minus in zip(
            voltages_ref_plus_raw.voltages,
            voltages_ref_minus_raw.voltages,
            strict=True,
        ):
            voltages_ref_raw.append(plus - minus)

        voltages_ref_raw: VoltageSamplingV2 = VoltageSamplingV2.from_list(
            voltages=voltages_ref_raw,
            input_frequency=freq.frequency,
            sampling_frequency=freq.sampling_frequency,
        )
        voltages_ref.append(voltages_ref_raw)

        voltages_dut_plus_raw_db = db.get_sweep_voltages(freq.id, channels[2].id)
        voltages_dut_plus_raw = VoltageSamplingV2.from_list(
            voltages_dut_plus_raw_db.voltages,
            input_frequency=freq.frequency,
            sampling_frequency=freq.sampling_frequency,
        )
        voltages_dut_plus.append(voltages_dut_plus_raw)

        voltages_dut_minus_raw_db = db.get_sweep_voltages(freq.id, channels[3].id)
        voltages_dut_minus_raw = VoltageSamplingV2.from_list(
            voltages_dut_minus_raw_db.voltages,
            input_frequency=freq.frequency,
            sampling_frequency=freq.sampling_frequency,
        )
        voltages_dut_minus.append(voltages_dut_minus_raw)

        voltages_dut_raw: list[float] = []
        for plus, minus in zip(
            voltages_dut_plus_raw.voltages,
            voltages_dut_minus_raw.voltages,
            strict=True,
        ):
            voltages_dut_raw.append(plus - minus)

        voltages_dut_raw: VoltageSamplingV2 = VoltageSamplingV2.from_list(
            voltages=voltages_dut_raw,
            input_frequency=freq.frequency,
            sampling_frequency=freq.sampling_frequency,
        )
        voltages_dut.append(voltages_dut_raw)

        debug: bool = False

        if debug:
            import matplotlib.pyplot as plt

            plt.plot(voltages_ref_raw.times, voltages_ref_raw.voltages, color="red")
            plt.plot(
                voltages_ref_plus_raw.times,
                voltages_ref_plus_raw.voltages,
                color="green",
            )
            plt.plot(
                voltages_ref_minus_raw.times,
                voltages_ref_minus_raw.voltages,
                color="blue",
            )
            plt.show()
            plt.close()

    make_balanced_graph_dB_phase(
        sweep_id=sweep_id,
        frequencies=frequencies,
        voltages_ref=voltages_ref,
        voltages_dut=voltages_dut,
        dB_offset=dB_offset,
    )


def make_balanced_graph_dB_phase(
    sweep_id: int,
    frequencies: list[DbFrequency],
    voltages_ref: list[VoltageSamplingV2],
    voltages_dut: list[VoltageSamplingV2],
    dB_offset: float = 0,
):
    log.info("make_graph_dB_phase")

    directory = Path(APP_HOME / "data/imgs")
    directory.mkdir(parents=True, exist_ok=True)

    timer = Timer()

    timer.start()

    figure, axis = plt.subplots(2, 1)
    figure.set_size_inches(15, 9)
    figure.tight_layout(pad=5.0)

    timer_lap = timer.lap()
    log.info(f"TIME INIT PLOT: {timer_lap}")

    comment = Prompt.ask("Test condition", default=None)
    timer_lap = timer.lap()
    plt.suptitle(f"ID: {sweep_id}, dB: {dB_offset:0.5f}, comment: {comment}")
    plt.style.use("seaborn")

    console.print(Panel("[bold]CREATING PLOT[/]"))

    interpolation_rate_rms = 50

    # Ref
    rms_ref: list[float] = []

    for volt_ref in voltages_ref:
        rms = RMS.rms_v3(
            volt_ref.augment_interpolation(
                interpolation_rate=interpolation_rate_rms,
                interpolation_mode=INTERPOLATION_KIND.CUBIC,
            ),
            trim=True,
            rms_mode=RMS_MODE.FFT,
        )
        rms_ref.append(rms)

    timer_lap = timer.lap()
    log.info(f"TIME CALCULATION REF RMS: {timer_lap}")

    # DUT
    rms_dut: list[RMSResult] = []
    for volt_dut in voltages_dut:
        rms = RMS.rms_v3(
            volt_dut.augment_interpolation(
                interpolation_rate=interpolation_rate_rms,
                interpolation_mode=INTERPOLATION_KIND.CUBIC,
            ),
            trim=True,
            rms_mode=RMS_MODE.FFT,
        )
        rms_dut.append(rms)

    timer_lap = timer.lap()
    log.info(f"TIME CALCULATION DUT RMS: {timer_lap}")

    axis_dut_sub_ref_dB: Axes = axis[0]
    axis_dut_sub_ref_dB.set_title("DUT - Ref [dB]")
    axis_dut_sub_ref_dB.set_xlabel("Frequency")
    axis_dut_sub_ref_dB.set_ylabel("dB")
    axis_dut_sub_ref_dB.tick_params(labelright=True)

    rms_dut_sub_ref_dB: list[float] = [
        calculate_gain_dB(ref, dut) - dB_offset for ref, dut in zip(rms_ref, rms_dut)
    ]

    (
        axis_dut_sub_ref_dB_data_x,
        axis_dut_sub_ref_dB_data_y,
    ) = logx_interpolation_model_smoothing_spline(
        [freq.frequency for freq in frequencies],
        rms_dut_sub_ref_dB,
        1,
        lam=0.00001,
    )

    #     axis_dut_sub_ref_dB_data_x,
    #     axis_dut_sub_ref_dB_data_y,
    # ) = logx_interpolation_model(
    #     rms_dut_sub_ref_dB,

    axis_dut_sub_ref_dB.semilogx(
        [freq.frequency for freq in frequencies],
        rms_dut_sub_ref_dB,
        ".",
        color="blue",
        markersize=3,
    )
    axis_dut_sub_ref_dB.semilogx(
        axis_dut_sub_ref_dB_data_x,
        axis_dut_sub_ref_dB_data_y,
        "-",
        color="red",
        linewidth=1,
    )
    if min(axis_dut_sub_ref_dB_data_y) < -3:
        axis_dut_sub_ref_dB.axhline(0, color="black", linewidth=1)
        axis_dut_sub_ref_dB.axhline(-3, color="green", linewidth=1)

    axis_dut_sub_ref_dB.axes.xaxis.set_minor_formatter(ticker.NullFormatter())
    axis_dut_sub_ref_dB.axes.xaxis.set_major_formatter(ticker.ScalarFormatter())
    axis_dut_sub_ref_dB.grid(which="major", color="grey", linestyle="-")
    axis_dut_sub_ref_dB.grid(which="minor", color="grey", linestyle="--")

    timer_lap = timer.lap()
    log.info(f"TIME DUT - REF dB PLOT: {timer_lap}")

    # DUT - Red [Phase °]
    axis_dut_sub_ref_phase_ax1: Axes = axis[1]
    axis_dut_sub_ref_phase_ax1.set_title("DUT - REF Phase [°]")
    axis_dut_sub_ref_phase_ax1.set_xlabel("Frequency")
    axis_dut_sub_ref_phase_ax1.set_ylabel("Degrees [°]")
    axis_dut_sub_ref_phase_ax1.tick_params(labelright=True)
    axis_dut_sub_ref_phase_ax1.axhline(0, color="black", linewidth=1)

    offset_phase_ref_dut: list[float] = []

    interpolation_rate_phase = 50

    for _freq, volts_ref, volts_dut in zip(
        frequencies,
        voltages_dut,
        voltages_ref,
        strict=True,
    ):
        voltage_sampling_ref = volts_ref.augment_interpolation(
            interpolation_rate=interpolation_rate_phase,
            interpolation_mode=INTERPOLATION_KIND.CUBIC,
        )

        voltage_sampling_dut = volts_dut.augment_interpolation(
            interpolation_rate=interpolation_rate_phase,
            interpolation_mode=INTERPOLATION_KIND.CUBIC,
        )

        try:
            offset_phase = phase_offset_v4(
                voltage_sampling_ref,
                voltage_sampling_dut,
            )
        except Exception as e:
            console.log(f"{e}")

            plt.close()
            plt.plot(voltage_sampling_ref.voltages, ".-", color="blue")
            plt.plot(voltage_sampling_dut.voltages, ".-", color="red")
            plt.show()
            plt.close()

        offset_phase_ref_dut.append(offset_phase)

    # --------------------------------------
    # for idx in range(1, len(sign_phase_list)):

    #     if is_cross:
    #         if (
    #             curr_sign_phase - prev_sign_phase < 0
    #             and abs(offset_phase_ref_dut[idx - 1] - offset_phase_ref_dut[idx]) > 100
    #         ):

    # for index_transform in index_to_transform:

    #     for idx, phase_value in enumerate(offset_phase_ref_dut):
    #         if idx <= index_transform:

    # for idx in range(1, len(sign_phase_list)):

    #     if is_cross:
    #         if (
    #             curr_sign_phase - prev_sign_phase > 0
    #             and abs(offset_phase_ref_dut[idx - 1] - offset_phase_ref_dut[idx]) > 100
    #         ):

    # for index_transform in index_to_transform:

    #     for idx, phase_value in enumerate(offset_phase_ref_dut):
    #         if idx <= index_transform:
    # --------------------------------------

    # TODO: V2
    # for idx in range(1, len(offset_phase_ref_dut)):

    #     if curr_sign_phase - prev_sign_phase:
    #         if (
    #             curr_sign_phase - prev_sign_phase > 0
    #             and abs(offset_phase_ref_dut[idx - 1] - offset_phase_ref_dut[idx]) > 100
    #         ):

    # TODO: V1
    for idx, value in enumerate(offset_phase_ref_dut):
        if value > 180:
            offset_phase_ref_dut[idx] -= 360

    (
        axis_dut_sub_ref_dB_data_x,
        axis_dut_sub_ref_dB_data_y,
    ) = logx_interpolation_model_smoothing_spline(
        [freq.frequency for freq in frequencies],
        offset_phase_ref_dut,
        1,
        lam=0.00001,
    )

    #     axis_dut_sub_ref_dB_data_x,
    #     axis_dut_sub_ref_dB_data_y,
    # ) = logx_interpolation_model(
    #     offset_phase_ref_dut,
    axis_dut_sub_ref_phase_ax1.semilogx(
        [freq.frequency for freq in frequencies],
        offset_phase_ref_dut,
        ".",
        color="blue",
        markersize=3,
    )
    axis_dut_sub_ref_phase_ax1.semilogx(
        axis_dut_sub_ref_dB_data_x,
        axis_dut_sub_ref_dB_data_y,
        "-",
        color="red",
        linewidth=1,
    )

    data_phase_y_max = max(offset_phase_ref_dut)
    data_phase_y_min = min(offset_phase_ref_dut)

    data_phase_y_range_max: int
    data_phase_y_range_min: int

    if data_phase_y_max < 30:
        data_phase_y_range_max = 30
    elif data_phase_y_max < 45:
        data_phase_y_range_max = 45
    elif data_phase_y_max <= 90:
        data_phase_y_range_max = 90
    elif data_phase_y_max <= 180:
        data_phase_y_range_max = 180
    else:
        data_phase_y_range_max = data_phase_y_max

    if data_phase_y_min > -30:
        data_phase_y_range_min = -30
    elif data_phase_y_min > -45:
        data_phase_y_range_min = -45
    elif data_phase_y_min >= -90:
        data_phase_y_range_min = -90
    elif data_phase_y_min >= -180:
        data_phase_y_range_min = -180
    else:
        data_phase_y_range_min = data_phase_y_min

    data_phase_y_total_range = int(data_phase_y_range_max - data_phase_y_range_min)

    data_phase_y_total_range_step: int = 5

    if data_phase_y_total_range <= 60:
        data_phase_y_total_range_step = 3
    elif data_phase_y_total_range <= 120:
        data_phase_y_total_range_step = 5
    elif data_phase_y_total_range <= 240:
        data_phase_y_total_range_step = 10
    elif data_phase_y_total_range <= 360:
        data_phase_y_total_range_step = 15
    else:
        data_phase_y_total_range_step = int(data_phase_y_total_range % 120) * 5

    axis_dut_sub_ref_phase_ax1.set_yticks(
        np.arange(
            data_phase_y_range_min,
            data_phase_y_range_max + 1,
            data_phase_y_total_range_step,
            dtype=int,
        ),
    )

    axis_dut_sub_ref_phase_ax1.axes.xaxis.set_minor_formatter(ticker.NullFormatter())
    axis_dut_sub_ref_phase_ax1.axes.xaxis.set_major_formatter(ticker.ScalarFormatter())
    axis_dut_sub_ref_phase_ax1.grid(which="major", color="grey", linestyle="-")
    axis_dut_sub_ref_phase_ax1.grid(which="minor", color="grey", linestyle="--")

    timer_lap = timer.lap()
    log.info(f"TIME DUT - REF PHASE PLOT: {timer_lap}")

    elapsed_time = timer.stop()
    log.info(f"TIME TOTAL: {elapsed_time}")

    file = directory / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')}.jpeg"
    plt.savefig(file)

    with open(file, mode="rb") as f:
        response = requests.post(
            "http://127.0.0.1:8090/api/collections/graphs/records",
            data={
                "sweep_id": sweep_id,
                "gain_dB": dB_offset,
                "comment": comment,
            },
            files={"file": f},
            timeout=5,
        )
        if response.status_code != 200:
            data = json.loads(response.content)
            console.log(data)

    plt.show()
    plt.close()


def test_balanced_calculation():
    make_balanced_calculation(
        sweep_id=268,
        dB_offset=-0.65613,
    )
