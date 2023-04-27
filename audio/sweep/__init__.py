import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

import pandas as pd
import requests
from rich.progress import track
from rich.table import Column, Table

from audio.config.sweep import SweepConfig
from audio.console import console
from audio.constant import APP_HOME
from audio.database.db import Database
from audio.device.cdaq import Ni9223
from audio.logging import log
from audio.math.algorithm import LogarithmicScale
from audio.math.rms import RMS
from audio.math.voltage import calculate_gain_db
from audio.model.sampling import VoltageSampling
from audio.usb.usbtmc import ResourceManager
from audio.utility import trim_value
from audio.utility.scpi import SCPI, Bandwidth, ScpiV2, Switch
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
            f"{frequency:.2f}",
            f"{Fs:.2f}",
            f"{number_of_samples}",
            f"{amplitude_peak_to_peak}",
            f"{rms:.5f} ",
            "[{}]{:.2f}[/]".format("red" if gain_dBV <= 0 else "green", gain_dBV),
            f"[cyan]{sampling_time}[/]",
            f"[cyan]{calculation_time}[/]",
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

    scpi = ScpiV2()

    if not generator.instr.connected:
        generator.open()

    # Sets the Configuration for the Voltmeter
    generator.execute(
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
        ],
    )
    generator.execute(
        [
            SCPI.set_output(1, Switch.ON),
        ],
    )

    log_scale: LogarithmicScale = LogarithmicScale(
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
    )

    frequency: float = round(config.sampling.frequency_min, 5)

    nidaq = Ni9223(
        config.sampling.number_of_samples,
        input_channel=config.nidaq.channels,
    )
    config.nidaq.max_frequency_sampling = nidaq.device.ai_max_multi_chan_rate

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.max_frequency_sampling,
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
    db.insert_sweep_config_data(
        sweep_id,
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
        config.sampling.number_of_samples,
        config.sampling.Fs_multiplier,
        config.sampling.delay_measurements,
    )

    channel_ids: list[int] = []

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
            else DEFAULT.get("delay"),
        )

        # Trim number_of_samples to MAX value
        Fs = trim_value(
            frequency * config.sampling.Fs_multiplier,
            max_value=config.nidaq.max_frequency_sampling,
        )

        # GET MEASUREMENTS
        nidaq.set_sampling_clock_timing(Fs)
        nidaq.task_start()
        timer.start()
        voltages = nidaq.read_multi_voltages()
        timer.stop()
        nidaq.task_stop()

        frequency_id = db.insert_frequency(sweep_id, idx, frequency, Fs)

        sweep_voltages_ids: list[int] = []

        for channel, voltages_sweep in zip(channel_ids, voltages):
            _id = db.insert_sweep_voltages(
                frequency_id,
                channel,
                voltages_sweep,
            )
            sweep_voltages_ids.append(_id)

    generator.execute(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )


def sweep(
    test_id: int,
    PB_test_id: str,
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

    scpi = ScpiV2()

    if not generator.instr.connected:
        generator.open()

    # Sets the Configuration for the Voltmeter
    generator.execute(
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
        ],
    )
    generator.execute(
        [
            SCPI.set_output(1, Switch.ON),
        ],
    )

    sleep(2)

    log_scale: LogarithmicScale = LogarithmicScale(
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
    )

    frequency: float = round(config.sampling.frequency_min, 5)

    nidaq = Ni9223(
        config.sampling.number_of_samples,
        input_channel=[ch.name for ch in config.nidaq.channels],
    )

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.max_frequency_sampling,
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
    db.insert_sweep_config_data(
        sweep_id,
        config.rigol.amplitude_peak_to_peak,
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
        config.sampling.number_of_samples,
        config.sampling.Fs_multiplier,
        config.sampling.delay_measurements,
    )

    PB_sweeps_id: str | None = None
    url = "http://127.0.0.1:8090/api/collections/sweeps/records"
    response = requests.post(
        url,
        json={
            "test_id": PB_test_id,
            "name": "Sweep v2 Procedure",
            "comment": "v2 Sweep Comment",
        },
        timeout=5,
    )
    response_data = json.loads(response.content.decode())
    console.log(response_data)
    if response.status_code != 200:
        console.log(f"[RESPONSE ERROR]: {url}")
    else:
        PB_sweeps_id = response_data["id"]

    channel_ids: list[int] = []
    PB_channels_ids: list[str] = []

    if config.nidaq.channels is None:
        return None

    for idx_channel, channel in enumerate(config.nidaq.channels):
        _id = db.insert_channel(
            sweep_id=sweep_id,
            idx=idx_channel,
            name=channel.name,
            comment=channel.comment,
        )
        channel_ids.append(_id)

        PB_channels_id: str | None = None
        url = "http://127.0.0.1:8090/api/collections/channels/records"
        response = requests.post(
            url,
            json={
                "sweep_id": PB_sweeps_id,
                "idx": idx_channel,
                "name": channel.name,
                "comment": channel.comment,
            },
            timeout=5,
        )
        response_data = json.loads(response.content.decode())
        console.log(response_data)
        if response.status_code != 200:
            console.log(f"[RESPONSE ERROR]: {url}")
        else:
            PB_channels_id = response_data["id"]

        PB_channels_ids.append(PB_channels_id)

    for idx_frequency, frequency in track(
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
            else DEFAULT.get("delay"),
        )

        time_sleep = timer.lap()

        # Trim number_of_samples to MAX value
        Fs = trim_value(
            frequency * config.sampling.Fs_multiplier,
            max_value=config.nidaq.max_frequency_sampling,
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

        frequency_id = db.insert_frequency(sweep_id, idx_frequency, frequency, Fs)

        time_db_insert_frequency = timer.lap()

        sweep_voltages_ids: list[int] = []

        for channel, voltages_sweep in zip(channel_ids, voltages, strict=True):
            _id = db.insert_sweep_voltages(
                frequency_id,
                channel,
                voltages_sweep,
            )
            sweep_voltages_ids.append(_id)

        directory = Path(APP_HOME / "data/measurements")
        directory.mkdir(parents=True, exist_ok=True)

        for PK_channel_id, voltage_data in zip(
            PB_channels_ids,
            voltages,
            strict=True,
        ):
            file = directory / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')}.csv"
            pd.DataFrame(voltage_data, columns=["voltage"]).to_csv(file)

            url = "http://127.0.0.1:8090/api/collections/measurements/records"
            json_data = {
                "sweep_id": PB_sweeps_id,
                "channel_id": PK_channel_id,
                "idx": idx_frequency,
                "frequency": frequency,
                "sampling_frequency": Fs,
            }
            console.log(json_data)
            response = requests.post(
                url,
                data=json_data,
                files={
                    "samples": Path.open(file, "rb"),
                },
                timeout=5,
            )
            response_data = json.loads(response.content.decode())
            console.log(response_data)
            if response.status_code != 200:
                console.log(f"[RESPONSE ERROR]: {url}")
            else:
                response_data["id"]

        time_db_insert_sweep_voltage = timer.lap()

        timer.stop()
        time_stop = time.perf_counter()
        console.log(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs} time: {timedelta(seconds=time_stop-time_start)}",
        )

        log.debug(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs}, {time_generator_write_frequency}, {time_trim}, {time_sleep}, {time_db_insert_frequency}, {time_db_insert_sweep_voltage}, {time_acquisition_set_clock}, {time_acquisition_task_start}, {time_acquisition_read}, {time_acquisition_task_stop}",
        )

    generator.execute(
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

    scpi = ScpiV2()

    if not generator.instr.connected:
        generator.open()

    # Sets the Configuration for the Voltmeter
    generator.execute(
        [
            scpi.reset,
            SCPI.reset(),
            SCPI.clear(),
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_function_voltage_ac(),
            SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
            SCPI.set_source_voltage_amplitude(1, round(amplitude_peak_to_peak, 5)),
            SCPI.set_source_frequency(1, round(frequency, 5)),
        ],
    )
    generator.execute(
        [
            SCPI.set_output(1, Switch.ON),
        ],
    )

    sleep(2)

    nidaq = Ni9223(
        config.sampling.number_of_samples,
        input_channel=[ch.name for ch in config.nidaq.channels],
    )

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.max_frequency_sampling,
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
            else DEFAULT.get("delay"),
        )

        timer.lap()

        # GET MEASUREMENTS
        nidaq.task_start()
        voltages = nidaq.read_multi_voltages()
        nidaq.task_stop()
        time_acquisition_read = timer.lap()

        log.debug(f"[DATA]: {len(voltages)}, {len(voltages[0])}, {len(voltages[1])}")

        timer.stop()
        time_stop = time.perf_counter()

        voltage_ref = VoltageSampling.from_list(
            voltages=voltages[0],
            input_frequency=frequency,
            sampling_frequency=Fs,
        )
        voltage_dut = VoltageSampling.from_list(
            voltages=voltages[1],
            input_frequency=frequency,
            sampling_frequency=Fs,
        )

        rms_result_ref = RMS.rms_v2(voltage_ref, trim=True, interpolation_rate=50)
        rms_result_dut = RMS.rms_v2(voltage_dut, trim=True, interpolation_rate=50)
        rms_ref_list.append(rms_result_ref.rms)
        rms_dut_list.append(rms_result_dut.rms)
        gain_dB = calculate_gain_db(rms_result_ref.rms, rms_result_dut.rms)
        rms_ref_sub_dut_list_dB.append(gain_dB)

        console.log(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs} time: {timedelta(seconds=time_stop-time_start)}",
        )

        console.log(
            f"[CALCULATION]: rms_ref: {rms_result_ref.rms}, rms_dut: {rms_result_dut.rms}, dB: {gain_dB}",
        )

        log.debug(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs}, {time_acquisition_read}",
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
        calculate_gain_db(Vin=rms_ref_list[-1], Vout=rms_dut_list[-1]),
    )

    console.log(f"[DATA]: average dB: {rms_ref_sub_dut_list_dB[-1]}")

    generator.execute(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )

    return rms_ref_sub_dut_list_dB[-1]


def sweep_balanced_single(
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

    scpi = ScpiV2()

    if not generator.instr.connected:
        generator.open()

    # Sets the Configuration for the Voltmeter
    generator.execute(
        [
            scpi.reset,
            SCPI.reset(),
            SCPI.clear(),
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_function_voltage_ac(),
            SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
            SCPI.set_source_voltage_amplitude(1, round(amplitude_peak_to_peak, 5)),
            SCPI.set_source_frequency(1, round(frequency, 5)),
        ],
    )
    generator.execute(
        [
            SCPI.set_output(1, Switch.ON),
        ],
    )

    sleep(2)

    nidaq = Ni9223(
        config.sampling.number_of_samples,
        input_channel=[ch.name for ch in config.nidaq.channels],
    )

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.max_frequency_sampling,
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
            else DEFAULT.get("delay"),
        )

        timer.lap()

        # GET MEASUREMENTS
        nidaq.task_start()
        voltages = nidaq.read_multi_voltages()
        nidaq.task_stop()
        time_acquisition_read = timer.lap()

        log.debug(f"[DATA]: {len(voltages)}, {len(voltages[0])}, {len(voltages[1])}")

        timer.stop()
        time_stop = time.perf_counter()

        voltage_ref_plus = VoltageSampling.from_list(
            voltages=voltages[0],
            input_frequency=frequency,
            sampling_frequency=Fs,
        )
        voltage_ref_minus = VoltageSampling.from_list(
            voltages=voltages[1],
            input_frequency=frequency,
            sampling_frequency=Fs,
        )
        voltage_dut_plus = VoltageSampling.from_list(
            voltages=voltages[2],
            input_frequency=frequency,
            sampling_frequency=Fs,
        )
        voltage_dut_minus = VoltageSampling.from_list(
            voltages=voltages[3],
            input_frequency=frequency,
            sampling_frequency=Fs,
        )

        voltage_ref_raw: list[float] = []
        for plus, minus in zip(
            voltage_ref_plus.voltages,
            voltage_ref_minus.voltages,
            strict=True,
        ):
            voltage_ref_raw.append(plus - minus)

        voltage_ref = VoltageSampling.from_list(
            voltages=voltage_ref_raw,
            input_frequency=frequency,
            sampling_frequency=Fs,
        )

        voltage_dut_raw: list[float] = []
        for plus, minus in zip(
            voltage_dut_plus.voltages,
            voltage_dut_minus.voltages,
            strict=True,
        ):
            voltage_dut_raw.append(plus - minus)

        voltage_dut = VoltageSampling.from_list(
            voltages=voltage_dut_raw,
            input_frequency=frequency,
            sampling_frequency=Fs,
        )

        rms_result_ref = RMS.rms_v2(voltage_ref, trim=True, interpolation_rate=50)
        rms_result_dut = RMS.rms_v2(voltage_dut, trim=True, interpolation_rate=50)
        rms_ref_list.append(rms_result_ref.rms)
        rms_dut_list.append(rms_result_dut.rms)
        gain_dB = calculate_gain_db(rms_result_ref.rms, rms_result_dut.rms)
        rms_ref_sub_dut_list_dB.append(gain_dB)

        console.log(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs} time: {timedelta(seconds=time_stop-time_start)}",
        )

        console.log(
            f"[CALCULATION]: rms_ref: {rms_result_ref.rms}, rms_dut: {rms_result_dut.rms}, dB: {gain_dB}",
        )

        log.debug(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs}, {time_acquisition_read}",
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
        calculate_gain_db(Vin=rms_ref_list[-1], Vout=rms_dut_list[-1]),
    )

    console.log(f"[DATA]: average dB: {rms_ref_sub_dut_list_dB[-1]}")

    generator.execute(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )

    return rms_ref_sub_dut_list_dB[-1]


def sweep_balanced(
    test_id: int,
    PB_test_id: str,
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

    scpi = ScpiV2()

    if not generator.instr.connected:
        generator.open()

    # Sets the Configuration for the Voltmeter
    generator.execute(
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
        ],
    )
    generator.execute(
        [
            SCPI.set_output(1, Switch.ON),
        ],
    )

    sleep(2)

    log_scale: LogarithmicScale = LogarithmicScale(
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
    )

    frequency: float = round(config.sampling.frequency_min, 5)

    nidaq = Ni9223(
        config.sampling.number_of_samples,
        input_channel=[ch.name for ch in config.nidaq.channels],
    )

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.max_frequency_sampling,
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
    db.insert_sweep_config_data(
        sweep_id,
        config.rigol.amplitude_peak_to_peak,
        config.sampling.frequency_min,
        config.sampling.frequency_max,
        config.sampling.points_per_decade,
        config.sampling.number_of_samples,
        config.sampling.Fs_multiplier,
        config.sampling.delay_measurements,
    )

    PB_sweeps_id: str | None = None
    url = "http://127.0.0.1:8090/api/collections/sweeps/records"
    response = requests.post(
        url,
        json={
            "test_id": PB_test_id,
            "name": "Sweep v2 Procedure",
            "comment": "v2 Sweep Comment",
        },
        timeout=5,
    )
    response_data = json.loads(response.content.decode())
    console.log(response_data)
    if response.status_code != 200:
        console.log(f"[RESPONSE ERROR]: {url}")
    else:
        PB_sweeps_id = response_data["id"]

    channel_ids: list[int] = []
    PB_channels_ids: list[str] = []

    if config.nidaq.channels is None:
        return None

    for idx_channel, channel in enumerate(config.nidaq.channels):
        _id = db.insert_channel(
            sweep_id=sweep_id,
            idx=idx_channel,
            name=channel.name,
            comment=channel.comment,
        )
        channel_ids.append(_id)

        PB_channels_id: str | None = None
        url = "http://127.0.0.1:8090/api/collections/channels/records"
        response = requests.post(
            url,
            json={
                "sweep_id": PB_sweeps_id,
                "idx": idx_channel,
                "name": channel.name,
                "comment": channel.comment,
            },
            timeout=5,
        )
        response_data = json.loads(response.content.decode())
        if response.status_code != 200:
            console.log(f"[RESPONSE ERROR]: {url}")
        else:
            PB_channels_id = response_data["id"]

        PB_channels_ids.append(PB_channels_id)

    BANDS: list[tuple[float, float, float]] = [
        (0, 10, 200),
        (10, 50, 1_000),
        (50, 100, 5_000),
        (100, 500, 10_000),
        (500, 1_000, 50_000),
        (1_000, 5_000, 100_000),
        (5_000, 10_000, 500_000),
        (10_000, 100_000, 1_000_000),
        (100_000, 1_000_000, 1_000_000),
    ]

    for idx_frequency, frequency in track(
        enumerate(log_scale.f_list),
        total=len(log_scale.f_list),
        console=console,
    ):
        time_start: float = timer.start()

        # Sets the Frequency
        generator.write(
            SCPI.set_source_frequency(1, round(frequency, 5)),
        )

        time_generator_write_frequency: timedelta = timer.lap()

        sleep(
            config.sampling.delay_measurements
            if config.sampling.delay_measurements is not None
            else DEFAULT.get("delay"),
        )

        time_sleep: timedelta = timer.lap()

        # Trim number_of_samples to MAX value
        new_sampling_frequency: float = 0.0

        for band in BANDS:
            low_band, high_band, band_sampling_frequency = band
            if frequency >= low_band and frequency < high_band:
                new_sampling_frequency = trim_value(
                    band_sampling_frequency,
                    max_value=config.nidaq.max_frequency_sampling,
                )

        if new_sampling_frequency == 0.0:
            sys.exit()

        # GET MEASUREMENTS
        if Fs != new_sampling_frequency:
            Fs = new_sampling_frequency
            nidaq.set_sampling_clock_timing(Fs)
        time_acquisition_set_clock = timer.lap()
        nidaq.task_start()
        time_acquisition_task_start = timer.lap()
        voltages = nidaq.read_multi_voltages()
        log.debug(f"[DATA]: {len(voltages)}, {len(voltages[0])}, {len(voltages[1])}")
        time_acquisition_read = timer.lap()
        nidaq.task_stop()
        time_acquisition_task_stop = timer.lap()

        frequency_id = db.insert_frequency(sweep_id, idx_frequency, frequency, Fs)

        time_db_insert_frequency = timer.lap()

        sweep_voltages_ids: list[int] = []

        for channel, voltages_sweep in zip(channel_ids, voltages, strict=True):
            _id = db.insert_sweep_voltages(
                frequency_id,
                channel,
                voltages_sweep,
            )
            sweep_voltages_ids.append(_id)

        directory = Path(APP_HOME / "data/measurements")
        directory.mkdir(parents=True, exist_ok=True)

        for PK_channel_id, voltage_data in zip(PB_channels_ids, voltages, strict=True):
            file = directory / f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%SZ')}.csv"
            pd.DataFrame(voltage_data).to_csv(file)

            url = "http://127.0.0.1:8090/api/collections/measurements/records"
            json_data = {
                "sweep_id": PB_sweeps_id,
                "channel_id": PK_channel_id,
                "idx": idx_frequency,
                "frequency": frequency,
                "sampling_frequency": Fs,
            }
            response = requests.post(
                url,
                data=json_data,
                files={
                    "samples": Path.open(file, "rb"),
                },
                timeout=5,
            )
            response_data = json.loads(response.content.decode())
            if response.status_code != 200:
                console.log(f"[RESPONSE ERROR]: {url}")
            else:
                response_data["id"]

        time_db_insert_sweep_voltage = timer.lap()

        timer.stop()
        time_stop = time.perf_counter()
        console.log(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs} time: {timedelta(seconds=time_stop-time_start)}",
        )

        log.debug(
            f"[ACQUISITION]: freq: {frequency}, Fs: {Fs}, {time_generator_write_frequency}, {time_sleep}, {time_db_insert_frequency}, {time_db_insert_sweep_voltage}, {time_acquisition_set_clock}, {time_acquisition_task_start}, {time_acquisition_read}, {time_acquisition_task_stop}",
        )

    generator.execute(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )

    return sweep_id
