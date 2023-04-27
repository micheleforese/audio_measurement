import datetime
import sys
from dataclasses import dataclass
from pathlib import Path
from time import sleep

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.figure import Figure
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
from usbtmc import Instrument

from audio.config.plot import PlotConfig
from audio.config.sweep import SweepConfig
from audio.console import console
from audio.device.cdaq import Ni9223
from audio.math import calculate_voltage_decibel, percentage_error, transfer_function
from audio.math.algorithm import LogarithmicScale
from audio.math.interpolation import InterpolationKind, logx_interpolation_model
from audio.math.pid import PidController, TimedValue
from audio.math.rms import RMS, RMS_MODE, RMSResult
from audio.math.voltage import VdBu_to_Vrms, Vpp_to_Vrms, calculate_gain_db
from audio.model.sampling import VoltageSampling, VoltageSamplingV2
from audio.model.sweep import SweepData
from audio.usb.usbtmc import ResourceManager, UsbTmc
from audio.utility import trim_value
from audio.utility.scpi import SCPI, Bandwidth, Switch
from audio.utility.timer import Timer


def sampling_curve(
    config: SweepConfig,
    sweep_home_path: Path,
    sweep_file_path: Path,
    debug: bool = False,
):
    """Sweep Function.

    Directory:
    `sweep_home_path`
    |-`/sweep`
        |- `1000`

        |- `2000`

        |- ...

        |- `10000`
    |-`sweep_file_path`: `/sweep.csv`

    Args:
        config (SweepConfigXML): Configurations.
        sweep_home_path (Path): Home for the sweep measurements
        sweep_file_path (Path): File path to the sweep `.csv` file
        debug (bool, optional): _description_. Defaults to False.
    """

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

    table = Table(
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

    live_group = Group(
        Panel(
            Group(
                table,
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
        list_devices: list[Instrument] = UsbTmc.search_devices()

        if len(list_devices) < 1:
            raise Exception("UsbTmc devices not found.")

        if debug:
            UsbTmc.print_devices_list(list_devices)

        generator: UsbTmc = UsbTmc(list_devices[0])

    except Exception as e:
        console.print(f"{e}")

    progress_list_task.update(task_sampling, task="Setting Devices")

    if not generator.instr.instrument.connected:
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
            config.sampling.number_of_samples = trim_value(
                config.sampling.number_of_samples,
                config.sampling.number_of_samples_max,
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

        sweep_frequency_path = measurements_path / "{}".format(
            round(frequency, 5),
        ).replace(".", "_", 1)
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
        result: RMSResult = RMS.rms_v2(voltages_sampling)
        voltages_sampling.save(save_file_path)

        elapsed_time: datetime.timedelta = time.stop()

        if result.rms:
            max_voltage = max(result.voltages)
            min_voltage = min(result.voltages)

            rms_list.append(result.rms)

            progress_sweep.update(
                task_sweep,
                frequency=f"{round(frequency, 5)}",
                rms=f"{round(result.rms, 5)}",
            )

            gain_bBV: float = calculate_voltage_decibel(
                input_voltage=Vpp_to_Vrms(config.rigol.amplitude_peak_to_peak),
                output_voltage=result.rms,
            )

            transfer_func_dB = transfer_function(
                result.rms,
                Vpp_to_Vrms(config.rigol.amplitude_peak_to_peak),
            )

            if max_dB:
                max_dB = max(abs(max_dB), abs(transfer_func_dB))
            else:
                max_dB = transfer_func_dB

            table.add_row(
                f"{frequency:.2f}",
                f"{Fs:.2f}",
                f"{config.sampling.number_of_samples}",
                f"{config.rigol.amplitude_peak_to_peak}",
                f"{round(result.rms, 5):.5f} ",
                "[{}]{:.2f}[/]".format(
                    "red" if gain_bBV <= 0 else "green",
                    transfer_func_dB,
                ),
                f"[cyan]{elapsed_time}[/]",
                f"{max_voltage:.5f}",
                f"{min_voltage:.5f}",
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
                n_samples_list,
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


def plot_from_csv(
    measurements_file_path: Path,
    plot_file_path: Path,
    file_offset_sweep_path: Path | None = None,
    plot_config: PlotConfig | None = None,
    debug: bool = False,
):
    progress_list_task = Progress(
        SpinnerColumn(),
        "•",
        TextColumn(
            "[bold blue]{task.description}[/] - [bold green]{task.fields[task]}[/]",
        ),
        transient=True,
    )

    live_group = Group(Panel(progress_list_task))

    live = Live(
        live_group,
        transient=True,
        console=console,
    )
    live.start()

    task_plotting = progress_list_task.add_task("Plotting", task="Plotting")
    progress_list_task.start_task(task_plotting)

    x_frequency: list[float] = []
    y_dBV: list[float] = []

    progress_list_task.update(task_plotting, task="Read Measurements")

    sweep_data = SweepData.from_csv_file(measurements_file_path)

    cfg = sweep_data.config

    if file_offset_sweep_path is not None:
        balancer = SweepData.from_csv_file(file_offset_sweep_path)

        sweep_data.data["dBV"] = sweep_data.data["dBV"] - balancer.data["dBV"]

        sweep_data.save(measurements_file_path.with_suffix(".balanced.csv"))

    if cfg.y_offset:
        sweep_data.data["dBV"] = sweep_data.data["dBV"] - cfg.y_offset

    x_frequency = list(sweep_data.frequency.values)
    y_dBV = list(sweep_data.dBV.values)

    progress_list_task.update(task_plotting, task="Apply Offset")

    sweep_data.config.override(new_config=plot_config)

    if debug:
        console.print(
            Panel(
                f"min dB: {min(y_dBV)}\n"
                + f"max dB: {max(y_dBV)}\n"
                + f"diff dB: {abs(max(y_dBV) - min(y_dBV))}",
            ),
        )

    progress_list_task.update(task_plotting, task="Interpolate")

    plot: tuple[Figure, Axes] = plt.subplots(
        figsize=(16 * 2, 9 * 2),
        dpi=cfg.dpi if cfg.dpi else 300,
    )

    fig: Figure
    axes: Axes

    fig, axes = plot

    x_interpolated, y_interpolated = logx_interpolation_model(
        x_frequency,
        y_dBV,
        int(
            len(x_frequency)
            * (cfg.interpolation_rate if cfg.interpolation_rate is not None else 5),
        ),
        kind=InterpolationKind.CUBIC,
    )

    xy_sampled = [x_frequency, y_dBV, "o"]
    xy_interpolated = [x_interpolated, y_interpolated, "-"]

    progress_list_task.update(task_plotting, task="Plotting Graph")

    axes.semilogx(
        *xy_sampled,
        *xy_interpolated,
        linewidth=4,
        color=cfg.color if cfg.color is not None else "yellow",
        label=cfg.legend,
    )

    axes.legend(
        loc="best",
    )

    # Added Line to y = -3
    axes.axhline(y=-3, linestyle="-", color="green")

    axes.set_title(
        "Frequency response",
        fontsize=50,
    )
    axes.set_xlabel(
        "Frequency ($Hz$)",
        fontsize=40,
    )
    axes.set_ylabel(
        "Amplitude ($dB$) ($0 \\, dB = {} \\, Vpp$)".format(
            round(cfg.y_offset, 5) if cfg.y_offset else 0,
        ),
        fontsize=40,
    )

    axes.tick_params(
        axis="both",
        labelsize=22,
    )
    axes.tick_params(axis="x", rotation=90)

    granularity_ticks = 0.1

    if (max(x_interpolated) / min(x_interpolated)) <= 3.3:
        granularity_ticks = 0.01

    logLocator = ticker.LogLocator(subs=np.arange(0, 1, granularity_ticks))

    def logMinorFormatFunc(x, pos):
        return f"{x:.0f}"

    logMinorFormat = ticker.FuncFormatter(logMinorFormatFunc)

    # X Axis - Major
    axes.xaxis.set_major_locator(logLocator)
    axes.xaxis.set_major_formatter(logMinorFormat)

    axes.grid(True, linestyle="-", which="both", color="0.7")

    if cfg.y_limit:
        axes.set_ylim(cfg.y_limit.min_value, cfg.y_limit.max_value)
    else:
        pass
        # TODO: Check for Nan or Inf Values
        # axes.set_ylim(
        #     min_y_dBV - 1,
        #     max_y_dBV + 1,

    plt.tight_layout()

    plt.savefig(plot_file_path)

    console.print(
        Panel(
            '[bold][[blue]FILE[/blue] - [cyan]GRAPH[/cyan]][/bold] - "[bold green]{}[/bold green]"'.format(
                plot_file_path.absolute().resolve(),
            ),
        ),
    )

    progress_list_task.remove_task(task_plotting)

    live.stop()


def config_set_level(
    dBu: float,
    config: SweepConfig,
    plot_file_path: Path | None,
    set_level_file_path: Path | None = None,
    debug: bool = False,
):
    voltage_amplitude_start: float = 0.1
    voltage_amplitude = voltage_amplitude_start
    frequency = 1000
    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.max_frequency_sampling,
    )
    diff_voltage = 0.001
    target_Vrms = VdBu_to_Vrms(dBu)

    table = Table(
        Column("Iteration", justify="right"),
        Column(f"{dBu:.1f} dBu [Vrms]", justify="right"),
        Column("Vpp [Vpp]", justify="right"),
        Column("Rms Value [V]", justify="right"),
        Column("Diff Vpp [V]", justify="right"),
        Column("Gain [dB]", justify="right"),
        Column("Proportional Term [V]", justify="right"),
        Column("Integral Term [V]", justify="right"),
        Column("Differential Term [V]", justify="right"),
        Column("Error [%]", justify="right"),
        title="[blue]Configuration.",
    )

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

    live_group = Group(
        table,
        Panel(
            Group(
                progress_list_task,
                progress_sweep,
                progress_task,
            ),
        ),
    )

    live = Live(
        live_group,
        transient=False,
        console=console,
        vertical_overflow="visible",
    )
    live.start()

    task_sampling = progress_list_task.add_task(
        "CONFIGURING",
        start=False,
        task="Retrieving Devices",
    )
    progress_list_task.start_task(task_sampling)

    # Asks for the 2 instruments
    list_devices: list[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    progress_list_task.update(task_sampling, task="Setting Devices")

    # Open the Instruments interfaces
    # Auto Close with the destructor
    generator.open()

    # Sets the Configuration for the Voltmeter
    generator_configs: list = [
        SCPI.clear(),
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_function_voltage_ac(),
        SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
        SCPI.set_source_voltage_amplitude(1, voltage_amplitude),
        SCPI.set_source_frequency(1, frequency),
    ]

    SCPI.exec_commands(generator, generator_configs)

    sleep(2)

    generator_ac_curves: list[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    progress_list_task.update(task_sampling, task="Searching for Voltage offset")

    Vpp_found: bool = False
    iteration: int = 0
    pid = PidController(
        set_point=target_Vrms,
        controller_gain=1.5,
        tau_integral=1,
        tau_derivative=0.5,
        controller_output_zero=voltage_amplitude_start,
    )

    gain_dB_list: list[float] = []

    k_tot = 0.2745
    gain_apparato: float | None = None

    nidaq = Ni9223(
        config.sampling.number_of_samples,
        Fs,
        input_channel=[config.nidaq.input_channel],
    )

    nidaq.create_task()
    nidaq.add_ai_channel(["cDAQ9189-1CDBE0AMod5/ai1"])
    nidaq.set_sampling_clock_timing(Fs)

    while not Vpp_found:
        # GET MEASUREMENTS
        nidaq.task_start()
        voltages = nidaq.read_single_voltages()
        nidaq.task_stop()
        voltages_sampling = VoltageSampling.from_list(voltages, frequency, Fs)
        result: RMSResult = RMS.rms_v2(
            voltages_sampling,
        )

        if result.rms is not None:
            if not gain_apparato:
                gain_apparato = result.rms / voltage_amplitude_start
                pid.controller_gain = k_tot / gain_apparato

            pid.add_process_variable(result.rms)

            error: float = target_Vrms - result.rms

            pid.add_error(TimedValue(error))

            error_percentage: float = percentage_error(
                exact=target_Vrms,
                approx=result.rms,
            )

            gain_dB: float = calculate_gain_db(
                result.rms,
                Vpp_to_Vrms(voltage_amplitude),
            )

            gain_dB_list.append(gain_dB)

            table.add_row(
                f"{iteration}",
                f"{target_Vrms:.8f}",
                f"{voltage_amplitude:.8f}",
                f"{result.rms:.8f}",
                "[{}]{:+.8f}[/]".format(
                    "red" if error > diff_voltage else "green",
                    error,
                ),
                "[{}]{:+.8f}[/]".format(
                    "red" if gain_dB < 0 else "green",
                    gain_dB,
                ),
                f"{pid.term.proportional[-1]:+.8f}",
                f"{pid.term.integral[-1]:+.8f}",
                f"{pid.term.derivative[-1]:+.8f}",
                "[{}]{:+.5%}[/]".format(
                    "red" if error > diff_voltage else "green",
                    error_percentage,
                ),
            )

            if pid.check_limit_diff(error, diff_voltage):
                Vpp_found = True

                table_result = Table(
                    "Gain Apparato",
                    "Kc",
                    "tauI",
                    "tauD",
                    "steps",
                )

                table_result.add_row(
                    f"{result.rms / voltage_amplitude:.8f}",
                    f"{pid.controller_gain}",
                    f"{pid.tau_integral}",
                    f"{pid.tau_derivative}",
                    f"{iteration}",
                )

                console.print(Panel(table_result))

            else:
                pid.term.add_proportional(pid.proportional_term)
                pid.term.add_integral(pid.integral_term)
                pid.term.add_derivative(pid.derivative_term)

                output_variable: float = pid.output_process

                pid.add_process_output(output_variable)

                voltage_amplitude = output_variable

                # Apply new Amplitude

                if voltage_amplitude > 11:
                    voltage_amplitude = 11
                    console.print("[ERROR] - Voltage Input > 11.", style="error")

                generator_configs: list = [
                    SCPI.set_source_voltage_amplitude(1, voltage_amplitude),
                ]

                SCPI.exec_commands(generator, generator_configs)

                sleep(0.4)

                iteration += 1
        else:
            console.print("[SAMPLING] - Error retrieving rms_value.")

    nidaq.task_close()

    generator_ac_curves: list[str] = [
        SCPI.set_output(1, Switch.OFF),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)
    generator.close()

    live.stop()

    console.print(Panel(f"Generator Voltage to obtain +4dBu: {voltage_amplitude}"))

    sp = np.full(iteration, target_Vrms)

    plt.figure(1, figsize=(16, 9))

    plt.subplot(2, 2, 1)
    plt.plot(
        sp,
        "k-",
        linewidth=0.5,
        label="Setpoint (SP)",
    )
    plt.plot(
        pid.process_variable_list,
        "r:",
        linewidth=1,
        label="Process Variable (PV)",
    )
    plt.grid(True)
    plt.legend(["Set Point (SP)", "Process Variable (PV)"], loc="best")

    plt.subplot(2, 2, 2)
    plt.plot(
        pid.term.proportional,
        color="g",
        linestyle="-",
        linewidth=2,
        label=r"Proportional = $K_c \; e(t)$",
    )
    plt.plot(
        pid.term.integral,
        color="b",
        linestyle="-",
        linewidth=2,
        label=r"Integral = $\frac{K_c}{\tau_I} \int_{i=0}^{n_t} e(t) \; dt $",
    )
    plt.plot(
        pid.term.derivative,
        color="r",
        linestyle="--",
        linewidth=2,
        label=r"Derivative = $-K_c \tau_D \frac{d(PV)}{dt}$",
    )
    plt.grid(True)
    plt.legend(loc="best")

    plt.subplot(2, 2, 3)
    plt.plot(
        [error.value for error in pid.error_list],
        color="m",
        linestyle="--",
        linewidth=2,
        label="Error (e=SP-PV)",
    )
    plt.grid(True)
    plt.legend(loc="best")

    plt.subplot(2, 2, 4)
    plt.plot(
        pid.process_output_list,
        color="b",
        linestyle="--",
        linewidth=2,
        label="Controller Output (OP)",
    )
    plt.grid(True)
    plt.legend(loc="best")

    if plot_file_path is not None:
        plt.savefig(plot_file_path)
    else:
        plt.show()


@dataclass
class DataSetLevel:
    volts: float
    dB: float

    def __str__(self) -> str:
        return f"[DataSetLevel]: volts: {self.volts}, dB: {self.dB}"

    def __rich_repr__(self):
        yield "volts", self.volts
        yield "dB", self.dB


def config_set_level_v2(
    dBu: float,
    config: SweepConfig,
):
    data_set_level: DataSetLevel | None = None

    voltage_amplitude_start: float = 0.01
    voltage_amplitude = voltage_amplitude_start
    frequency = 1000
    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.max_frequency_sampling,
    )
    diff_voltage = 0.0005
    target_Vrms = VdBu_to_Vrms(dBu)
    interpolation_rate_rms: float = 50

    table = Table(
        Column("Iteration", justify="right"),
        Column(f"{dBu:.1f} dBu [Vrms]", justify="right"),
        Column("Vpp [Vpp]", justify="right"),
        Column("Rms Value [V]", justify="right"),
        Column("Diff Vpp [V]", justify="right"),
        Column("Gain [dB]", justify="right"),
        Column("Proportional Term [V]", justify="right"),
        Column("Integral Term [V]", justify="right"),
        Column("Differential Term [V]", justify="right"),
        Column("Error [%]", justify="right"),
        title="[blue]Configuration.",
    )

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

    live_group = Group(
        table,
        Panel(
            Group(
                progress_list_task,
                progress_sweep,
                progress_task,
            ),
        ),
    )

    live = Live(
        live_group,
        transient=False,
        console=console,
        vertical_overflow="visible",
    )
    live.start()

    task_sampling = progress_list_task.add_task(
        "CONFIGURING",
        start=False,
        task="Retrieving Devices",
    )
    progress_list_task.start_task(task_sampling)

    # Asks for the 2 instruments
    isSwitchedOn: bool = False
    rm = ResourceManager()

    while not isSwitchedOn:
        devices = rm.search_resources()
        if len(devices) == 0:
            live.console.log("RIGOL NOT FOUND")
            live.console.log("Connect Rigol.")
            sleep(3)
        else:
            isSwitchedOn = True

    generator = rm.open_resource(device=devices[0])

    progress_list_task.update(task_sampling, task="Setting Devices")

    # Open the Instruments interfaces
    # Auto Close with the destructor
    generator.open()

    # Sets the Configuration for the Voltmeter
    generator_configs: list = [
        SCPI.clear(),
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_function_voltage_ac(),
        SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
        SCPI.set_source_voltage_amplitude(1, voltage_amplitude),
        SCPI.set_source_frequency(1, frequency),
    ]

    SCPI.exec_commands(generator, generator_configs)

    sleep(2)

    generator_ac_curves: list[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    progress_list_task.update(task_sampling, task="Searching for Voltage offset")

    Vpp_found: bool = False
    iteration: int = 0
    pid = PidController(
        set_point=target_Vrms,
        controller_gain=1.5,
        tau_integral=1,
        tau_derivative=0.5,
        controller_output_zero=voltage_amplitude_start,
    )

    gain_dB_list: list[float] = []

    k_tot = 0.2745
    gain_apparato: float | None = None

    level_offset: float | None = None

    nidaq = Ni9223(
        config.sampling.number_of_samples,
        Fs,
        input_channel=[ch.name for ch in config.nidaq.channels],
    )

    nidaq.create_task()
    nidaq.add_ai_channel([ch.name for ch in config.nidaq.channels])
    nidaq.set_sampling_clock_timing(Fs)

    while not Vpp_found:
        # GET MEASUREMENTS
        nidaq.task_start()

        isVoltagesRetrievingOk = False
        while isVoltagesRetrievingOk is not True:
            voltages = nidaq.read_multi_voltages()
            if voltages is None:
                console.log("[ERROR]: Error in retrieving Samples.")
            else:
                isVoltagesRetrievingOk = True

        nidaq.task_stop()

        voltages_sampling_ref = VoltageSampling.from_list(voltages[0], frequency, Fs)
        voltages_sampling_dut = VoltageSampling.from_list(voltages[1], frequency, Fs)

        rms_ref: RMSResult = RMS.rms_v2(
            voltages_sampling_ref,
            interpolation_rate=interpolation_rate_rms,
            trim=True,
        )
        rms_dut: RMSResult = RMS.rms_v2(
            voltages_sampling_dut,
            interpolation_rate=interpolation_rate_rms,
            trim=True,
        )

        if rms_ref is None or rms_dut is None:
            console.log("[ERROR]: rms_not calculated")

        if rms_dut.rms is not None:
            if not gain_apparato:
                gain_apparato = rms_dut.rms / voltage_amplitude_start
                pid.controller_gain = k_tot / gain_apparato

            pid.add_process_variable(rms_dut.rms)

            error: float = target_Vrms - rms_dut.rms

            pid.add_error(TimedValue(error))

            error_percentage: float = percentage_error(
                exact=target_Vrms,
                approx=rms_dut.rms,
            )

            gain_dB: float = calculate_gain_db(rms_ref.rms, rms_dut.rms)

            gain_dB_list.append(gain_dB)

            table.add_row(
                f"{iteration}",
                f"{target_Vrms:.8f}",
                f"{voltage_amplitude:.8f}",
                f"{rms_dut.rms:.8f}",
                "[{}]{:+.8f}[/]".format(
                    "red" if error > diff_voltage else "green",
                    error,
                ),
                "[{}]{:+.8f}[/]".format(
                    "red" if gain_dB < 0 else "green",
                    gain_dB,
                ),
                f"{pid.term.proportional[-1]:+.8f}",
                f"{pid.term.integral[-1]:+.8f}",
                f"{pid.term.derivative[-1]:+.8f}",
                "[{}]{:+.5%}[/]".format(
                    "red" if error > diff_voltage else "green",
                    error_percentage,
                ),
            )

            if pid.check_limit_diff(error, diff_voltage):
                Vpp_found = True
                level_offset = voltage_amplitude

                table_result = Table(
                    "Gain Apparato",
                    "Kc",
                    "tauI",
                    "tauD",
                    "steps",
                )

                table_result.add_row(
                    f"{rms_dut.rms / voltage_amplitude:.8f}",
                    f"{pid.controller_gain}",
                    f"{pid.tau_integral}",
                    f"{pid.tau_derivative}",
                    f"{iteration}",
                )

                console.print(Panel(table_result))

                data_set_level = DataSetLevel(volts=level_offset, dB=gain_dB)

            else:
                pid.term.add_proportional(pid.proportional_term)
                pid.term.add_integral(pid.integral_term)
                pid.term.add_derivative(pid.derivative_term)

                output_variable: float = pid.output_process

                pid.add_process_output(output_variable)

                voltage_amplitude = output_variable

                # Apply new Amplitude

                if voltage_amplitude > 11:
                    voltage_amplitude = 11
                    console.print("[ERROR] - Voltage Input > 11.", style="error")

                generator_configs: list = [
                    SCPI.set_source_voltage_amplitude(1, voltage_amplitude),
                ]

                SCPI.exec_commands(generator, generator_configs)

                sleep(0.4)

                iteration += 1
        else:
            console.print("[SAMPLING] - Error retrieving rms_value.")

    nidaq.task_close()
    live.stop()

    generator_ac_curves: list[str] = [
        SCPI.set_output(1, Switch.OFF),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)
    generator.close()

    np.full(iteration, target_Vrms)

    return data_set_level


def plot_config_set_level_v2(
    sp: np.ndarray,
    pid: PidController,
    plot_file_path: Path,
):
    plt.figure(1, figsize=(16, 9))

    plt.subplot(2, 2, 1)
    plt.plot(
        sp,
        "k-",
        linewidth=0.5,
        label="Setpoint (SP)",
    )
    plt.plot(
        pid.process_variable_list,
        "r:",
        linewidth=1,
        label="Process Variable (PV)",
    )
    plt.grid(True)
    plt.legend(["Set Point (SP)", "Process Variable (PV)"], loc="best")

    plt.subplot(2, 2, 2)
    plt.plot(
        pid.term.proportional,
        color="g",
        linestyle="-",
        linewidth=2,
        label=r"Proportional = $K_c \; e(t)$",
    )
    plt.plot(
        pid.term.integral,
        color="b",
        linestyle="-",
        linewidth=2,
        label=r"Integral = $\frac{K_c}{\tau_I} \int_{i=0}^{n_t} e(t) \; dt $",
    )
    plt.plot(
        pid.term.derivative,
        color="r",
        linestyle="--",
        linewidth=2,
        label=r"Derivative = $-K_c \tau_D \frac{d(PV)}{dt}$",
    )
    plt.grid(True)
    plt.legend(loc="best")

    plt.subplot(2, 2, 3)
    plt.plot(
        [error.value for error in pid.error_list],
        color="m",
        linestyle="--",
        linewidth=2,
        label="Error (e=SP-PV)",
    )
    plt.grid(True)
    plt.legend(loc="best")

    plt.subplot(2, 2, 4)
    plt.plot(
        pid.process_output_list,
        color="b",
        linestyle="--",
        linewidth=2,
        label="Controller Output (OP)",
    )
    plt.grid(True)
    plt.legend(loc="best")

    plt.savefig(plot_file_path)


def config_balanced_set_level_v2(
    dBu: float,
    config: SweepConfig,
) -> DataSetLevel | None:
    data_set_level: DataSetLevel | None = None

    voltage_amplitude_start: float = 0.01
    voltage_amplitude: float = voltage_amplitude_start
    frequency = 1000
    Fs: float = trim_value(
        frequency * config.sampling.Fs_multiplier,
        max_value=config.nidaq.max_frequency_sampling,
    )
    diff_voltage = 0.0005
    target_Vrms: float = VdBu_to_Vrms(dBu)
    interpolation_rate_rms: float = 50

    table = Table(
        Column("Iteration", justify="right"),
        Column(f"{dBu:.1f} dBu [Vrms]", justify="right"),
        Column("Vpp [Vpp]", justify="right"),
        Column("Rms Value [V]", justify="right"),
        Column("Diff Vpp [V]", justify="right"),
        Column("Gain [dB]", justify="right"),
        Column("Proportional Term [V]", justify="right"),
        Column("Integral Term [V]", justify="right"),
        Column("Differential Term [V]", justify="right"),
        Column("Error [%]", justify="right"),
        title="[blue]Configuration.",
    )

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

    live_group = Group(
        table,
        Panel(
            Group(
                progress_list_task,
                progress_sweep,
                progress_task,
            ),
        ),
    )

    live = Live(
        live_group,
        transient=False,
        console=console,
        vertical_overflow="visible",
    )
    live.start()

    task_sampling = progress_list_task.add_task(
        "CONFIGURING",
        start=False,
        task="Retrieving Devices",
    )
    progress_list_task.start_task(task_sampling)

    # Asks for the 2 instruments
    isSwitchedOn: bool = False
    rm = ResourceManager()

    while not isSwitchedOn:
        devices = rm.search_resources()
        if len(devices) == 0:
            live.console.log("RIGOL NOT FOUND")
            live.console.log("Connect Rigol.")
            sleep(3)
        else:
            isSwitchedOn = True

    generator = rm.open_resource(device=devices[0])

    progress_list_task.update(task_sampling, task="Setting Devices")

    # Open the Instruments interfaces
    # Auto Close with the destructor
    generator.open()

    # Sets the Configuration for the Voltmeter
    generator_configs: list = [
        SCPI.clear(),
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_function_voltage_ac(),
        SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
        SCPI.set_source_voltage_amplitude(1, voltage_amplitude),
        SCPI.set_source_frequency(1, frequency),
    ]

    SCPI.exec_commands(generator, generator_configs)

    sleep(2)

    generator_ac_curves: list[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    progress_list_task.update(task_sampling, task="Searching for Voltage offset")

    Vpp_found: bool = False
    iteration: int = 0
    pid = PidController(
        set_point=target_Vrms,
        controller_gain=1.5,
        tau_integral=1,
        tau_derivative=0.2,
        controller_output_zero=voltage_amplitude_start,
    )

    gain_dB_list: list[float] = []

    k_tot = 0.2745
    gain_apparato: float | None = None

    level_offset: float | None = None

    nidaq = Ni9223(
        config.sampling.number_of_samples,
        Fs,
        input_channel=[ch.name for ch in config.nidaq.channels],
    )

    nidaq.create_task()
    nidaq.add_ai_channel([ch.name for ch in config.nidaq.channels])
    nidaq.set_sampling_clock_timing(Fs)

    while not Vpp_found:
        # GET MEASUREMENTS
        nidaq.task_start()

        isVoltagesRetrievingOk = False
        while isVoltagesRetrievingOk is not True:
            voltages: list[float] | None = nidaq.read_multi_voltages()
            if voltages is None:
                console.log("[ERROR]: Error in retrieving Samples.")
            else:
                isVoltagesRetrievingOk = True

        nidaq.task_stop()

        voltages_sampling_ref_plus = VoltageSamplingV2.from_list(
            voltages[0],
            frequency,
            Fs,
        )
        voltages_sampling_ref_minus = VoltageSamplingV2.from_list(
            voltages[1],
            frequency,
            Fs,
        )
        voltages_sampling_dut_plus = VoltageSamplingV2.from_list(
            voltages[2],
            frequency,
            Fs,
        )
        voltages_sampling_dut_minus = VoltageSamplingV2.from_list(
            voltages[3],
            frequency,
            Fs,
        )

        voltages_sampling_ref_raw: list[float] = []
        for plus, minus in zip(
            voltages_sampling_ref_plus.voltages,
            voltages_sampling_ref_minus.voltages,
            strict=True,
        ):
            voltages_sampling_ref_raw.append(plus - minus)

        voltages_sampling_ref: VoltageSamplingV2 = VoltageSamplingV2.from_list(
            voltages=voltages_sampling_ref_raw,
            input_frequency=frequency,
            sampling_frequency=Fs,
        ).augment_interpolation(
            interpolation_rate_rms,
            interpolation_mode=InterpolationKind.CUBIC,
        )

        voltages_sampling_dut_raw: list[float] = []
        for plus, minus in zip(
            voltages_sampling_dut_plus.voltages,
            voltages_sampling_dut_minus.voltages,
            strict=True,
        ):
            voltages_sampling_dut_raw.append(plus - minus)

        voltages_sampling_dut: VoltageSamplingV2 = VoltageSamplingV2.from_list(
            voltages=voltages_sampling_dut_raw,
            input_frequency=frequency,
            sampling_frequency=Fs,
        ).augment_interpolation(
            interpolation_rate_rms,
            interpolation_mode=InterpolationKind.CUBIC,
        )

        rms_ref: float = RMS.rms_v3(
            voltages_sampling_ref,
            trim=True,
            rms_mode=RMS_MODE.FFT,
        )
        rms_dut: float = RMS.rms_v3(
            voltages_sampling_dut,
            trim=True,
            rms_mode=RMS_MODE.FFT,
        )

        if rms_ref is None or rms_dut is None:
            console.log("[ERROR]: rms_not calculated")

        if rms_dut is not None:
            if not gain_apparato:
                gain_apparato = rms_dut / voltage_amplitude_start
                pid.controller_gain = k_tot / gain_apparato

            pid.add_process_variable(rms_dut)

            error: float = target_Vrms - rms_dut

            pid.add_error(TimedValue(error))

            error_percentage: float = percentage_error(
                exact=target_Vrms,
                approx=rms_dut,
            )

            gain_dB: float = calculate_gain_db(rms_ref, rms_dut)

            gain_dB_list.append(gain_dB)

            table.add_row(
                f"{iteration}",
                f"{target_Vrms:.8f}",
                f"{voltage_amplitude:.8f}",
                f"{rms_dut:.8f}",
                "[{}]{:+.8f}[/]".format(
                    "red" if error > diff_voltage else "green",
                    error,
                ),
                "[{}]{:+.8f}[/]".format(
                    "red" if gain_dB < 0 else "green",
                    gain_dB,
                ),
                f"{pid.term.proportional[-1]:+.8f}",
                f"{pid.term.integral[-1]:+.8f}",
                f"{pid.term.derivative[-1]:+.8f}",
                "[{}]{:+.5%}[/]".format(
                    "red" if error > diff_voltage else "green",
                    error_percentage,
                ),
            )

            if pid.check_limit_diff(error, diff_voltage):
                Vpp_found = True
                level_offset = voltage_amplitude

                table_result = Table(
                    "Gain Apparato",
                    "Kc",
                    "tauI",
                    "tauD",
                    "steps",
                )

                table_result.add_row(
                    f"{rms_dut / voltage_amplitude:.8f}",
                    f"{pid.controller_gain}",
                    f"{pid.tau_integral}",
                    f"{pid.tau_derivative}",
                    f"{iteration}",
                )

                console.print(Panel(table_result))

                data_set_level = DataSetLevel(volts=level_offset, dB=gain_dB)

            else:
                pid.term.add_proportional(pid.proportional_term)
                pid.term.add_integral(pid.integral_term)
                pid.term.add_derivative(pid.derivative_term)

                output_variable: float = pid.output_process

                pid.add_process_output(output_variable)

                voltage_amplitude = output_variable

                # Apply new Amplitude

                if voltage_amplitude > 11:
                    voltage_amplitude = 11
                    console.print("[ERROR] - Voltage Input > 11.", style="error")

                generator_configs: list = [
                    SCPI.set_source_voltage_amplitude(1, voltage_amplitude),
                ]

                SCPI.exec_commands(generator, generator_configs)

                sleep(0.4)

                iteration += 1
        else:
            console.print("[SAMPLING] - Error retrieving rms_value.")

    nidaq.task_close()
    live.stop()

    generator_ac_curves: list[str] = [
        SCPI.set_output(1, Switch.OFF),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)
    generator.close()

    np.full(iteration, target_Vrms)

    return data_set_level
