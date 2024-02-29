import sys
from datetime import timedelta
from pathlib import Path
from time import sleep

import pandas as pd
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Column, Table

from audio.config.sweep import SweepConfig
from audio.console import console
from audio.device.cdaq import Ni9223
from audio.math.algorithm import LogarithmicScale
from audio.math.rms import RMS, RMSResult
from audio.math.voltage import Vpp_to_Vrms
from audio.model.sampling import VoltageSampling
from audio.model.sweep import SweepData
from audio.usb.usbtmc import ResourceManager, UsbTmc
from audio.utility import trim_value
from audio.utility.scpi import SCPI, Bandwidth, Switch
from audio.utility.timer import Timer


class AmplitudeSweepTable:
    table: Table

    def __init__(self) -> None:
        self.table = Table(
            Column(r"Frequency [Hz]", justify="right"),
            Column(r"Fs [Hz]", justify="right"),
            Column("Number of samples", justify="right"),
            Column(r"Input Voltage [V]", justify="right"),
            Column(r"Rms Value [V]", justify="right"),
            Column(r"Gain [dB]", justify="right"),
            Column(r"Time [s]", justify="right"),
            Column(r"Max Voltage [V]", justify="right"),
            Column(r"Min Voltage [V]", justify="right"),
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
        time: timedelta,
        voltage_max: float,
        voltage_min: float,
    ):
        self.table.add_row(
            f"{frequency:.2f}",
            f"{Fs:.2f}",
            f"{number_of_samples}",
            f"{amplitude_peak_to_peak}",
            f"{rms:.5f} ",
            "[{}]{:.2f}[/]".format("red" if gain_dBV <= 0 else "green", gain_dBV),
            f"[cyan]{time}[/]",
            f"{voltage_max:.5f}",
            f"{voltage_min:.5f}",
        )


def amplitude_sweep(
    config: SweepConfig,
    sweep_home_path: Path,
    sweep_file_path: Path,
    debug: bool = False,
):
    DEFAULT = {"delay": 0.2}

    HOME: Path = sweep_home_path
    HOME.mkdir(parents=True, exist_ok=True)

    measurements_path: Path = HOME / "sweep"
    measurements_path.mkdir(parents=True, exist_ok=True)

    progress_list_task = Progress(
        SpinnerColumn(),
        "•",
        TextColumn(
            "[bold blue]{task.description}[/] - [bold green]{task.fields[task]}[/]",
        ),
        transient=True,
    )
    progress_sweep = Progress(
        SpinnerColumn(),
        "•",
        TextColumn(
            "[bold blue]{task.description}",
            justify="right",
        ),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        "•",
        TimeElapsedColumn(),
        "•",
        MofNCompleteColumn(),
        TextColumn(
            " - Frequency: [bold green]{task.fields[frequency]} - RMS: {task.fields[rms]}",
        ),
        console=console,
        transient=True,
    )
    progress_task = Progress(
        SpinnerColumn(),
        "•",
        TextColumn(
            "[bold blue]{task.description}",
        ),
        transient=True,
    )

    amplitude_sweep_table = AmplitudeSweepTable()

    live_group = Group(
        Panel(
            Group(
                amplitude_sweep_table.table,
                progress_list_task,
                progress_sweep,
                progress_task,
            ),
        ),
    )
    live = Live(
        live_group,
        transient=True,
        console=console,
        vertical_overflow="visible",
    )
    live.start()

    task_sampling = progress_list_task.add_task(
        "Sampling",
        start=False,
        task="Retrieving Devices",
    )
    progress_list_task.start_task(task_sampling)

    # Asks for the 2 instruments
    try:
        rm = ResourceManager()
        list_devices = rm.search_resources()

        if len(list_devices) < 1:
            raise Exception("UsbTmc devices not found.")

        if debug:
            UsbTmc.print_devices_list(list_devices)
        generator = rm.open_resource(list_devices[0])

    except Exception as e:
        console.print(f"{e}")

    progress_list_task.update(task_sampling, task="Setting Devices")

    if not generator.instr.connected:
        generator.open()

    if config.rigol.amplitude_peak_to_peak > 12:
        generator.execute(
            [
                SCPI.set_output(1, Switch.OFF),
            ],
        )
        generator.close()
        console.print("[ERROR] - Voltage Input > 12.", style="error")
        sys.exit()

    # Sets the Configuration for the Voltmeter
    generator.execute(
        [
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

    frequency_list: list[float] = []
    rms_list: list[float] = []
    dBV_list: list[float] = []
    fs_list: list[float] = []
    oversampling_ratio_list: list[float] = []
    n_periods_list: list[float] = []
    n_samples_list: list[int] = []

    frequency: float = round(config.sampling.frequency_min, 5)

    max_dB: float | None = None

    progress_list_task.update(task_sampling, task="Sweep")

    task_sweep = progress_sweep.add_task(
        "Sweep",
        start=False,
        total=len(log_scale.f_list),
        frequency="",
        rms="",
    )
    progress_sweep.start_task(task_sweep)

    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.max_frequency_sampling,
    )

    nidaq = Ni9223(
        config.sampling.number_of_samples,
        input_channel=[config.nidaq.input_channel],
    )

    nidaq.create_task("Sampling")
    nidaq.add_ai_channel([config.nidaq.input_channel])
    nidaq.set_sampling_clock_timing(Fs)

    for frequency in log_scale.f_list:
        # Sets the Frequency
        generator.write(SCPI.set_source_frequency(1, round(frequency, 5)))

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

        # Trim number_of_samples to MAX value
        if config.sampling.number_of_samples_max is not None and (
            config.sampling.number_of_samples > config.sampling.number_of_samples_max
        ):
            config.sampling.number_of_samples = int(
                trim_value(
                    config.sampling.number_of_samples,
                    config.sampling.number_of_samples_max,
                ),
            )

        oversampling_ratio = Fs / frequency
        n_periods = config.sampling.number_of_samples / oversampling_ratio

        frequency_list.append(frequency)
        fs_list.append(Fs)
        oversampling_ratio_list.append(oversampling_ratio)
        n_periods_list.append(n_periods)
        n_samples_list.append(config.sampling.number_of_samples)

        time = Timer()
        time.start()

        sweep_frequency_path = measurements_path / f"{round(frequency, 5)}".replace(".", "_", 1)
        sweep_frequency_path.mkdir(parents=True, exist_ok=True)

        save_file_path = sweep_frequency_path / "sample.csv"

        # GET MEASUREMENTS

        nidaq.set_sampling_clock_timing(Fs)
        nidaq.task_start()
        voltages = nidaq.read_single_voltages()
        nidaq.task_stop()

        voltages_sampling = VoltageSampling.from_list(
            voltages,
            frequency,
            Fs,
        )
        result: RMSResult = RMS.rms_v2(
            voltages_sampling,
            trim=True,
            interpolation_rate=10,
        )
        voltages_sampling.save(save_file_path)

        elapsed_time: timedelta = time.stop()

        if result.rms:
            max_voltage = max(result.voltages)
            min_voltage = min(result.voltages)

            rms_list.append(result.rms)

            progress_sweep.update(
                task_sweep,
                frequency=f"{round(frequency, 5)}",
                rms=f"{round(result.rms, 5)}",
            )

            from audio.math.voltage import calculate_gain_db

            gain_bBV = calculate_gain_db(
                Vin=Vpp_to_Vrms(config.rigol.amplitude_peak_to_peak),
                Vout=result.rms,
            )
            # gain_bBV: float = dBV(

            max_dB = max(abs(max_dB), abs(gain_bBV)) if max_dB else gain_bBV

            amplitude_sweep_table.add_data(
                frequency=frequency,
                Fs=Fs,
                amplitude_peak_to_peak=config.rigol.amplitude_peak_to_peak,
                number_of_samples=config.sampling.number_of_samples,
                rms=result.rms,
                gain_dBV=gain_bBV,
                time=elapsed_time,
                voltage_max=max_voltage,
                voltage_min=min_voltage,
            )
            dBV_list.append(gain_bBV)

            progress_sweep.update(task_sweep, advance=1)

        else:
            console.print("[ERROR] - Error retrieving rms_value.", style="error")

    sampling_data = pd.DataFrame(
        list(
            zip(
                frequency_list,
                rms_list,
                dBV_list,
                fs_list,
                oversampling_ratio_list,
                n_periods_list,
                n_samples_list, strict=False,
            ),
        ),
        columns=[
            "frequency",
            "rms",
            "dBV",
            "fs",
            "oversampling_ratio",
            "n_periods",
            "n_samples",
        ],
    )

    sweep_data = SweepData(
        sampling_data,
        amplitude=config.rigol.amplitude_peak_to_peak,
        config=config.plot,
    )

    console.print(f"[FILE - SWEEP CSV] '{sweep_file_path}'")

    sweep_data.save(sweep_file_path)

    progress_sweep.remove_task(task_sweep)

    progress_list_task.update(task_sampling, task="Shutting down the Channel 1")

    generator.execute(
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )

    progress_list_task.remove_task(task_sampling)

    if debug:
        console.print(Panel(f"max_dB: {max_dB}"))

    console.print(
        Panel(
            f'[bold][[blue]FILE[/blue] - [cyan]CSV[/cyan]][/bold] - "[bold green]{sweep_file_path.absolute()}[/bold green]"',
        ),
    )

    live.stop()
