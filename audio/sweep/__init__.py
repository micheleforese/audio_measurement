import time
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from typing import List, Optional

import pandas as pd
from matplotlib.axes import Axes
from rich.panel import Panel
from rich.progress import track
from rich.table import Column, Table

from audio.config.sweep import SweepConfig
from audio.console import console
from audio.database.db import Database
from audio.device.cDAQ import ni9223
from audio.logging import log
from audio.math.algorithm import LogarithmicScale
from audio.math.rms import RMS, RMSResult, VoltageSampling
from audio.math.voltage import Vpp_to_Vrms, calculate_gain_dB
from audio.model.sampling import VoltageSampling
from audio.model.sweep import SweepData
from audio.usb.usbtmc import ResourceManager
from audio.utility import trim_value
from audio.utility.scpi import SCPI, Bandwidth, SCPI_v2, Switch
from audio.utility.timer import Timer


class SweepAmplitudePhaseTable:
    table: Table

    def __init__(self) -> None:
        self.table = Table(
            Column(r"Frequency [Hz]", justify="right"),
            Column(r"Fs [Hz]", justify="right"),
            Column(r"Number of samples", justify="right"),
            Column(r"Input Voltage [V]", justify="right"),
            Column(r"Rms Value [V]", justify="right"),
            Column(r"Gain [dB]", justify="right"),
            Column(r"Sampling Time[s]", justify="right"),
            Column(r"Calculation Time[s]", justify="right"),
            title="[blue]Sweep.",
        )

    def add_data(
        self,
        frequency: float,
        Fs: float,
        number_of_samples: int,
        amplitude_peak_to_peak: float,
        rms: float,
        gain_dBV: float,
        sampling_time: timedelta,
        calculation_time: timedelta,
    ):
        self.table.add_row(
            "{:.2f}".format(frequency),
            "{:.2f}".format(Fs),
            "{}".format(number_of_samples),
            "{}".format(amplitude_peak_to_peak),
            "{:.5f} ".format(rms),
            "[{}]{:.2f}[/]".format("red" if gain_dBV <= 0 else "green", gain_dBV),
            "[cyan]{}[/]".format(sampling_time),
            "[cyan]{}[/]".format(calculation_time),
        )


def sweep_amplitude_phase(
    config: SweepConfig,
):
    DEFAULT = {"delay": 0.2}

    db = Database()

    # Asks for the 2 instruments
    try:
        rm = ResourceManager()
        list_devices = rm.search_resources()
        if len(list_devices) < 1:
            raise Exception("UsbTmc devices not found.")
        generator = rm.open_resource(list_devices[0])

    except Exception as e:
        console.print(f"{e}")

    scpi = SCPI_v2()

    if not generator.instr.connected:
        generator.open()

    # Sets the Configuration for the Voltmeter
    generator.exec(
        [
            scpi.reset,
            SCPI.reset(),
            SCPI.clear(),
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_function_voltage_ac(),
            SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
            SCPI.set_source_voltage_amplitude(
                1,
                round(
                    config.rigol.amplitude_peak_to_peak,
                    5,
                ),
            ),
            SCPI.set_source_frequency(1, round(config.sampling.frequency_min, 5)),
        ]
    )
    generator.exec(
        [
            SCPI.set_output(1, Switch.ON),
        ]
    )

    log_scale: LogarithmicScale = LogarithmicScale(
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
    )

    frequency: float = round(config.sampling.frequency_min, 5)

    nidaq = ni9223(
        config.sampling.number_of_samples,
        input_channel=config.nidaq.channels,
    )
    config.nidaq.Fs_max = nidaq.device.ai_max_multi_chan_rate

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.Fs_max,
    )
    nidaq.create_task("Sweep Amplitude-Phase")
    nidaq.add_ai_channel(config.nidaq.channels)
    nidaq.set_sampling_clock_timing(Fs)

    timer = Timer()

    test_id = db.insert_test(
        "Sweep Amplitude Phase",
        datetime.now(),
        "Double sweep for Amplitude and Phase",
    )
    sweep_id = db.insert_sweep(
        test_id,
        "Sweep Amplitude and Phase",
        datetime.now(),
        "Sweep Input/Output",
    )
    db.insert_sweep_config(
        sweep_id,
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
        config.sampling.number_of_samples,
        config.sampling.Fs_multiplier,
        config.sampling.delay_measurements,
    )

    channel_ids: List[int] = []

    for idx, channel in enumerate(config.nidaq.channels):
        _id = db.insert_channel(
            sweep_id,
            idx,
            channel.name,
            comment=channel.comment,
        )
        channel_ids.append(_id)

    for idx, frequency in track(
        enumerate(log_scale.f_list),
        total=len(log_scale.f_list),
        console=console,
    ):

        # Sets the Frequency
        generator.write(
            SCPI.set_source_frequency(1, round(frequency, 5)),
        )

        sleep(
            config.sampling.delay_measurements
            if config.sampling.delay_measurements is not None
            else DEFAULT.get("delay")
        )

        # Trim number_of_samples to MAX value
        Fs = trim_value(
            frequency * config.sampling.Fs_multiplier,
            max_value=config.nidaq.Fs_max,
        )

        # GET MEASUREMENTS
        nidaq.set_sampling_clock_timing(Fs)
        nidaq.task_start()
        timer.start()
        voltages = nidaq.read_multi_voltages()
        sampling_time = timer.stop()
        nidaq.task_stop()

        frequency_id = db.insert_frequency(sweep_id, idx, frequency, Fs)

        sweep_voltages_ids: List[int] = []

        for channel, voltages_sweep in zip(channel_ids, voltages):

            _id = db.insert_sweep_voltages(
                frequency_id,
                channel,
                voltages_sweep,
            )
            sweep_voltages_ids.append(_id)

    generator.exec(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )


def sweep(
    test_id: int,
    config: SweepConfig,
):
    DEFAULT = {"delay": 0.2}

    db = Database()

    # Asks for the 2 instruments
    try:
        rm = ResourceManager()
        list_devices = rm.search_resources()
        if len(list_devices) < 1:
            raise Exception("UsbTmc devices not found.")
        generator = rm.open_resource(list_devices[0])

    except Exception as e:
        console.print(f"{e}")

    scpi = SCPI_v2()

    if not generator.instr.connected:
        generator.open()

    # Sets the Configuration for the Voltmeter
    generator.exec(
        [
            scpi.reset,
            SCPI.reset(),
            SCPI.clear(),
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_function_voltage_ac(),
            SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
            SCPI.set_source_voltage_amplitude(
                1,
                round(
                    config.rigol.amplitude_peak_to_peak,
                    5,
                ),
            ),
            SCPI.set_source_frequency(1, round(config.sampling.frequency_min, 5)),
        ]
    )
    generator.exec(
        [
            SCPI.set_output(1, Switch.ON),
        ]
    )

    sleep(2)

    log_scale: LogarithmicScale = LogarithmicScale(
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
    )

    frequency: float = round(config.sampling.frequency_min, 5)

    nidaq = ni9223(
        config.sampling.number_of_samples,
        input_channel=[ch.name for ch in config.nidaq.channels],
    )

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.Fs_max,
    )
    nidaq.create_task("Sweep")
    nidaq.add_ai_channel([ch.name for ch in config.nidaq.channels])
    nidaq.set_sampling_clock_timing(Fs)

    timer = Timer()

    sweep_id = db.insert_sweep(
        test_id,
        "Sweep Amplitude and Phase",
        datetime.now(),
        "Sweep Input/Output",
    )
    db.insert_sweep_config(
        sweep_id,
        config.rigol.amplitude_peak_to_peak,
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
        config.sampling.number_of_samples,
        config.sampling.Fs_multiplier,
        config.sampling.delay_measurements,
    )

    channel_ids: List[int] = []

    if config.nidaq.channels is None:
        return None

    for idx, channel in enumerate(config.nidaq.channels):
        _id = db.insert_channel(
            sweep_id=sweep_id,
            idx=idx,
            name=channel.name,
            comment=channel.comment,
        )
        channel_ids.append(_id)

    for idx, frequency in track(
        enumerate(log_scale.f_list),
        total=len(log_scale.f_list),
        console=console,
    ):
        time_start = timer.start()

        # Sets the Frequency
        generator.write(
            SCPI.set_source_frequency(1, round(frequency, 5)),
        )

        time_generator_write_frequency = timer.lap()

        sleep(
            config.sampling.delay_measurements
            if config.sampling.delay_measurements is not None
            else DEFAULT.get("delay")
        )

        time_sleep = timer.lap()

        # Trim number_of_samples to MAX value
        Fs = trim_value(
            frequency * config.sampling.Fs_multiplier,
            max_value=config.nidaq.Fs_max,
        )

        time_trim = timer.lap()

        # GET MEASUREMENTS
        nidaq.set_sampling_clock_timing(Fs)
        time_acquisition_set_clock = timer.lap()
        nidaq.task_start()
        time_acquisition_task_start = timer.lap()
        voltages = nidaq.read_multi_voltages()
        log.debug(f"[DATA]: {len(voltages)}, {len(voltages[0])}, {len(voltages[1])}")
        time_acquisition_read = timer.lap()
        nidaq.task_stop()
        time_acquisition_task_stop = timer.lap()

        frequency_id = db.insert_frequency(sweep_id, idx, frequency, Fs)

        time_db_insert_frequency = timer.lap()

        sweep_voltages_ids: List[int] = []

        for channel, voltages_sweep in zip(channel_ids, voltages):

            _id = db.insert_sweep_voltages(
                frequency_id,
                channel,
                voltages_sweep,
            )
            sweep_voltages_ids.append(_id)

        time_db_insert_sweep_voltage = timer.lap()

        timer.stop()
        time_stop = time.perf_counter()
        console.log(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs} time: {timedelta(seconds=time_stop-time_start)}"
        )

        log.debug(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs}, {time_generator_write_frequency}, {time_trim}, {time_sleep}, {time_db_insert_frequency}, {time_db_insert_sweep_voltage}, {time_acquisition_set_clock}, {time_acquisition_task_start}, {time_acquisition_read}, {time_acquisition_task_stop}"
        )

    generator.exec(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )

    return sweep_id


def sweep_single(
    amplitude_peak_to_peak: float,
    frequency: float,
    n_sweep: int,
    config: SweepConfig,
):
    DEFAULT = {"delay": 0.2}

    # Asks for the 2 instruments
    try:
        rm = ResourceManager()
        list_devices = rm.search_resources()
        if len(list_devices) < 1:
            raise Exception("UsbTmc devices not found.")
        generator = rm.open_resource(list_devices[0])

    except Exception as e:
        console.print(f"{e}")

    scpi = SCPI_v2()

    if not generator.instr.connected:
        generator.open()

    # Sets the Configuration for the Voltmeter
    generator.exec(
        [
            scpi.reset,
            SCPI.reset(),
            SCPI.clear(),
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_function_voltage_ac(),
            SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
            SCPI.set_source_voltage_amplitude(1, round(amplitude_peak_to_peak, 5)),
            SCPI.set_source_frequency(1, round(frequency, 5)),
        ]
    )
    generator.exec(
        [
            SCPI.set_output(1, Switch.ON),
        ]
    )

    sleep(2)

    nidaq = ni9223(
        config.sampling.number_of_samples,
        input_channel=[ch.name for ch in config.nidaq.channels],
    )

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.Fs_max,
    )
    nidaq.create_task("Sweep Single")
    nidaq.add_ai_channel([ch.name for ch in config.nidaq.channels])
    nidaq.set_sampling_clock_timing(Fs)

    timer = Timer()

    if config.nidaq.channels is None:
        return None

    rms_ref_list: list[float] = []
    rms_dut_list: list[float] = []
    rms_ref_sub_dut_list_dB: list[float] = []

    for _ in track(
        range(0, n_sweep),
        total=n_sweep,
        console=console,
    ):
        time_start = timer.start()

        sleep(
            config.sampling.delay_measurements
            if config.sampling.delay_measurements is not None
            else DEFAULT.get("delay")
        )

        time_sleep = timer.lap()

        # GET MEASUREMENTS
        nidaq.task_start()
        voltages = nidaq.read_multi_voltages()
        nidaq.task_stop()
        time_acquisition_read = timer.lap()

        log.debug(f"[DATA]: {len(voltages)}, {len(voltages[0])}, {len(voltages[1])}")

        timer.stop()
        time_stop = time.perf_counter()

        voltage_ref = VoltageSampling.from_list(
            voltages=voltages[0], input_frequency=frequency, sampling_frequency=Fs
        )
        voltage_dut = VoltageSampling.from_list(
            voltages=voltages[1], input_frequency=frequency, sampling_frequency=Fs
        )

        rms_result_ref = RMS.rms_v2(voltage_ref, trim=True, interpolation_rate=50)
        rms_result_dut = RMS.rms_v2(voltage_dut, trim=True, interpolation_rate=50)
        rms_ref_list.append(rms_result_ref.rms)
        rms_dut_list.append(rms_result_dut.rms)
        gain_dB = calculate_gain_dB(rms_result_ref.rms, rms_result_dut.rms)
        rms_ref_sub_dut_list_dB.append(gain_dB)

        console.log(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs} time: {timedelta(seconds=time_stop-time_start)}"
        )

        console.log(
            f"[CALCULATION]: rms_ref: {rms_result_ref.rms}, rms_dut: {rms_result_dut.rms}, dB: {gain_dB}"
        )

        log.debug(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs}, {time_acquisition_read}"
        )

    rms_ref_average = 0

    for rms_ref in rms_ref_list:
        rms_ref_average += rms_ref

    rms_ref_average /= len(rms_ref_list)

    rms_ref_list.append(rms_ref_average)

    rms_dut_average = 0

    for rms_dut in rms_dut_list:
        rms_dut_average += rms_dut

    rms_dut_average /= len(rms_dut_list)

    rms_dut_list.append(rms_dut_average)

    rms_ref_sub_dut_list_dB.append(
        calculate_gain_dB(Vin=rms_ref_list[-1], Vout=rms_dut_list[-1])
    )

    console.log(f"[DATA]: average dB: {rms_ref_sub_dut_list_dB[-1]}")

    generator.exec(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )
    # import matplotlib.pyplot as plt

    # figure, axes = plt.subplots(1, 2)

    # rms_plot: Axes = axes[0]
    # rms_plot.plot(rms_ref_list, "o", color="blue")
    # rms_plot.plot(rms_dut_list, "o", color="red")

    # dB_plot: Axes = axes[1]
    # dB_plot.plot(rms_ref_sub_dut_list_dB, "o", color="green")
    # plt.show()

    return rms_ref_sub_dut_list_dB[-1]
