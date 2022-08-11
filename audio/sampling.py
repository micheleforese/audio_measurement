from math import sqrt
from pathlib import Path
from time import sleep
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
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

import audio.ui.terminal as ui_t
from audio.config.plot import PlotConfigXML
from audio.config.sweep import SweepConfigXML
from audio.console import console
from audio.math import dBV, percentage_error, transfer_function
from audio.math.algorithm import LogarithmicScale
from audio.math.interpolation import INTERPOLATION_KIND, logx_interpolation_model
from audio.math.pid import PID_Controller, Timed_Value
from audio.math.rms import RMS
from audio.model.sweep import SweepData
from audio.usb.usbtmc import UsbTmc
from audio.utility import trim_value
from audio.utility.scpi import SCPI, Bandwidth, Switch
from audio.utility.timer import Timer, Timer_Message


def sampling_curve(
    config: SweepConfigXML,
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
            " - Frequency: [bold green]{task.fields[frequency]} - RMS: {task.fields[rms]}"
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
            )
        ),
    )
    live = Live(
        live_group,
        transient=True,
        console=console,
    )
    live.start()

    task_sampling = progress_list_task.add_task(
        "Sampling", start=False, task="Retrieving Devices"
    )
    progress_list_task.start_task(task_sampling)

    # Asks for the 2 instruments
    try:
        list_devices: List[Instrument] = UsbTmc.search_devices()

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

    # Sets the Configuration for the Voltmeter
    generator.exec(
        [
            SCPI.reset(),
            SCPI.clear(),
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_function_voltage_ac(),
            SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
            SCPI.set_source_voltage_amplitude(
                1,
                round(
                    config.rigol.amplitude_peak_to_peak
                    if config.rigol.amplitude_peak_to_peak < 5
                    else 0,
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

    frequency_list: List[float] = []
    rms_list: List[float] = []
    dBV_list: List[float] = []
    fs_list: List[float] = []
    oversampling_ratio_list: List[float] = []
    n_periods_list: List[float] = []
    n_samples_list: List[int] = []

    frequency: float = round(config.sampling.frequency_min, 5)

    max_dB: Optional[float] = None

    progress_list_task.update(task_sampling, task="Sweep")

    task_sweep = progress_sweep.add_task(
        "Sweep",
        start=False,
        total=len(log_scale.f_list),
        frequency="",
        rms="",
    )
    progress_sweep.start_task(task_sweep)

    for frequency in log_scale.f_list:

        # Sets the Frequency
        generator.write(SCPI.set_source_frequency(1, round(frequency, 5)))

        # TODO: Implement delay from config if it exists.
        sleep(0.2)

        # Trim number_of_samples to MAX value
        Fs = trim_value(
            frequency * config.sampling.Fs_multiplier, max_value=config.nidaq.Fs_max
        )

        # Trim number_of_samples to MAX value
        if config.sampling.number_of_samples_max is not None:
            if (
                config.sampling.number_of_samples
                > config.sampling.number_of_samples_max
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
            round(frequency, 5)
        ).replace(".", "_", 1)
        sweep_frequency_path.mkdir(parents=True, exist_ok=True)

        save_file_path = sweep_frequency_path / "sample.csv"

        # GET MEASUREMENTS
        voltages, rms_value = RMS.rms(
            Fs=Fs,
            ch_input=config.nidaq.input_channel,
            max_voltage=config.nidaq.voltage_max,
            min_voltage=config.nidaq.voltage_min,
            number_of_samples=config.sampling.number_of_samples,
            time_report=False,
            frequency=frequency,
            save_file=save_file_path,
        )

        message: Timer_Message = time.stop()

        if rms_value:
            max_voltage = max(voltages)
            min_voltage = min(voltages)

            rms_list.append(rms_value)

            progress_sweep.update(
                task_sweep,
                frequency=f"{round(frequency, 5)}",
                rms="{}".format(round(rms_value, 5)),
            )

            gain_bBV: float = dBV(
                V_in=config.rigol.amplitude_peak_to_peak / (2 * sqrt(2)),
                V_out=rms_value,
            )

            transfer_func_dB = transfer_function(
                rms_value, config.rigol.amplitude_peak_to_peak / (2 * np.math.sqrt(2))
            )

            if max_dB:
                max_dB = max(abs(max_dB), abs(transfer_func_dB))
            else:
                max_dB = transfer_func_dB

            table.add_row(
                "{:.2f}".format(frequency),
                "{:.2f}".format(Fs),
                "{}".format(config.sampling.number_of_samples),
                "{}".format(config.rigol.amplitude_peak_to_peak),
                "{:.5f} ".format(round(rms_value, 5)),
                "[{}]{:.2f}[/]".format(
                    "red" if gain_bBV <= 0 else "green", transfer_func_dB
                ),
                "[cyan]{}[/]".format(message.elapsed_time),
                "{:.5f}".format(max_voltage),
                "{:.5f}".format(min_voltage),
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
            )
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

    sweep_data = SweepData(sampling_data, amplitude=config.rigol.amplitude_peak_to_peak)

    sweep_data.save(measurements_path)

    if debug:
        console.print(table)

    progress_sweep.remove_task(task_sweep)

    progress_list_task.update(task_sampling, task="Shutting down the Channel 1")

    SCPI.exec_commands(
        generator,
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )

    progress_list_task.remove_task(task_sampling)

    if debug:
        console.print(Panel("max_dB: {}".format(max_dB)))

    console.print(
        Panel(
            f'[bold][[blue]FILE[/blue] - [cyan]CSV[/cyan]][/bold] - "[bold green]{sweep_file_path.absolute()}[/bold green]"'
        )
    )

    live.stop()


def plot_from_csv(
    measurements_file_path: Path,
    plot_file_path: Path,
    plot_config: Optional[PlotConfigXML] = None,
    debug: bool = False,
):

    live_group = Group(Panel(ui_t.progress_list_task))

    live = Live(
        live_group,
        transient=True,
        console=console,
    )
    live.start()

    task_plotting = ui_t.progress_list_task.add_task("Plotting", task="Plotting")
    ui_t.progress_list_task.start_task(task_plotting)

    x_frequency: List[float] = []
    y_dBV: List[float] = []

    ui_t.progress_list_task.update(task_plotting, task="Read Measurements")

    sweep_data = SweepData(measurements_file_path)

    cfg = sweep_data.config

    x_frequency = list(sweep_data.frequency.values)
    y_dBV = list(sweep_data.dBV.values)

    if debug:
        console.print(
            Panel(
                "min dB: {}\n".format(min(y_dBV))
                + "max dB: {}\n".format(max(y_dBV))
                + "diff dB: {}".format(abs(max(y_dBV) - min(y_dBV)))
            )
        )

    ui_t.progress_list_task.update(task_plotting, task="Apply Offset")

    sweep_data.config.override(new_config=plot_config)

    if cfg.y_offset:
        y_dBV = [dBV - cfg.y_offset for dBV in y_dBV]

    ui_t.progress_list_task.update(task_plotting, task="Interpolate")

    plot: Tuple[Figure, Axes] = plt.subplots(
        figsize=(16 * 2, 9 * 2), dpi=cfg.dpi if cfg.dpi else 300
    )

    fig: Figure
    axes: Axes

    fig, axes = plot

    x_interpolated, y_interpolated = logx_interpolation_model(
        x_frequency,
        y_dBV,
        int(
            len(x_frequency)
            * (cfg.interpolation_rate if cfg.interpolation_rate is not None else 5)
        ),
        kind=INTERPOLATION_KIND.CUBIC,
    )

    xy_sampled = [x_frequency, y_dBV, "o"]
    xy_interpolated = [x_interpolated, y_interpolated, "-"]

    ui_t.progress_list_task.update(task_plotting, task="Plotting Graph")

    axes.semilogx(
        *xy_sampled,
        *xy_interpolated,
        linewidth=4,
        color=cfg.color if cfg.color is not None else "yellow",
    )
    # Added Line to y = -3
    axes.plot(
        [0, max(x_interpolated)],
        [-3, -3],
        "-",
        color="green",
    )

    axes.set_title(
        "Frequency response",
        fontsize=50,
    )
    axes.set_xlabel(
        "Frequency ($Hz$)",
        fontsize=40,
    )
    axes.set_ylabel(
        "Amplitude ($dB$) ($0 \, dB = {} \, Vpp$)".format(
            round(cfg.y_offset, 5) if cfg.y_offset else 0
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
        return "{:.0f}".format(x)

    logMinorFormat = ticker.FuncFormatter(logMinorFormatFunc)

    # X Axis - Major
    axes.xaxis.set_major_locator(logLocator)
    axes.xaxis.set_major_formatter(logMinorFormat)

    axes.grid(True, linestyle="-", which="both", color="0.7")

    if cfg.y_limit:
        axes.set_ylim(cfg.y_limit.min, cfg.y_limit.max)
    else:
        min_y_dBV = min(y_interpolated)
        max_y_dBV = max(y_interpolated)
        axes.set_ylim(
            min_y_dBV - 1,
            max_y_dBV + 1,
        )

    plt.tight_layout()

    plt.savefig(plot_file_path)

    console.print(
        Panel(
            '[bold][[blue]FILE[/blue] - [cyan]GRAPH[/cyan]][/bold] - "[bold green]{}[/bold green]"'.format(
                plot_file_path.absolute().resolve()
            )
        )
    )

    ui_t.progress_list_task.remove_task(task_plotting)

    live.stop()


def config_set_level(
    config: SweepConfigXML,
    plot_file_path: Path,
    set_level_file_path: Optional[Path] = None,
    debug: bool = False,
):

    voltage_amplitude_start: float = 0.01
    voltage_amplitude = voltage_amplitude_start
    frequency = 1000
    Fs = trim_value(
        frequency * config.sampling.Fs_multiplier, max_value=config.nidaq.Fs_max
    )
    diff_voltage = 0.001
    Vpp_4dBu_exact = 1.227653

    table = Table(
        Column("Iteration", justify="right"),
        Column("4dBu [V]", justify="right"),
        Column("Vpp [V]", justify="right"),
        Column("Rms Value [V]", justify="right"),
        Column("Diff Vpp [V]", justify="right"),
        Column("Gain [dB]", justify="right"),
        Column("Proportional Term [V]", justify="right"),
        Column("Integral Term [V]", justify="right"),
        Column("Differential Term [V]", justify="right"),
        Column("Error [%]", justify="right"),
        title="[blue]Configuration.",
    )

    live_group = Group(
        table,
        Panel(
            Group(
                ui_t.progress_list_task,
                ui_t.progress_sweep,
                ui_t.progress_task,
            )
        ),
    )

    live = Live(
        live_group,
        transient=False,
        console=console,
        vertical_overflow="visible",
    )
    live.start()

    task_sampling = ui_t.progress_list_task.add_task(
        "CONFIGURING", start=False, task="Retrieving Devices"
    )
    ui_t.progress_list_task.start_task(task_sampling)

    # Asks for the 2 instruments
    list_devices: List[Instrument] = UsbTmc.search_devices()
    if debug:
        UsbTmc.print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    ui_t.progress_list_task.update(task_sampling, task="Setting Devices")

    # Open the Instruments interfaces
    # Auto Close with the destructor
    generator.open()

    # Sets the Configuration for the Voltmeter
    # Frequency: 1000
    generator_configs: list = [
        SCPI.clear(),
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_function_voltage_ac(),
        SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
        SCPI.set_source_voltage_amplitude(1, voltage_amplitude),
        SCPI.set_source_frequency(1, frequency),
    ]

    SCPI.exec_commands(generator, generator_configs)

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    # sleep(2)

    ui_t.progress_list_task.update(task_sampling, task="Searching for Voltage offset")

    Vpp_found: bool = False
    iteration: int = 0
    pid = PID_Controller(
        set_point=Vpp_4dBu_exact,
        controller_gain=1.5,
        tauI=1,
        tauD=0.5,
        controller_output_zero=voltage_amplitude_start,
    )

    gain_dB_list: List[float] = []

    k_tot = 0.2745
    gain_apparato: Optional[float] = None

    level_offset: Optional[float] = None

    while not Vpp_found:

        # GET MEASUREMENTS
        voltages, rms_value = RMS.rms(
            frequency=frequency,
            Fs=Fs,
            ch_input=config.nidaq.input_channel,
            max_voltage=config.nidaq.voltage_max,
            min_voltage=config.nidaq.voltage_min,
            number_of_samples=config.sampling.number_of_samples,
            # interpolation_rate=config.plot.interpolation_rate,
            time_report=False,
        )

        if rms_value:

            if not gain_apparato:
                gain_apparato = rms_value / voltage_amplitude_start
                pid.controller_gain = k_tot / gain_apparato

            pid.add_process_variable(rms_value)

            error: float = Vpp_4dBu_exact - rms_value

            pid.add_error(Timed_Value(error))

            error_percentage: float = percentage_error(
                exact=Vpp_4dBu_exact, approx=rms_value
            )

            gain_dB: float = 20 * np.log10(
                rms_value / (voltage_amplitude / (2 * sqrt(2)))
            )

            gain_dB_list.append(gain_dB)

            table.add_row(
                f"{iteration}",
                f"{Vpp_4dBu_exact:.8f}",
                f"{voltage_amplitude:.8f}",
                f"{rms_value:.8f}",
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
                    f"{rms_value / voltage_amplitude:.8f}",
                    f"{pid.controller_gain}",
                    f"{pid.tauI}",
                    f"{pid.tauD}",
                    f"{iteration}",
                )

                console.print(Panel(table_result))

                if set_level_file_path is None:
                    set_level_file_path = plot_file_path.with_suffix(".offset")

                f = open(set_level_file_path, "w", encoding="utf-8")
                f.write("{}\n".format(level_offset))
                f.write("{}\n".format(gain_dB))
                f.close()

                console.print(Panel("[PATH] - {}".format(set_level_file_path)))

            else:

                pid.term.add_proportional(pid.proportional_term)
                pid.term.add_integral(pid.integral_term)
                pid.term.add_derivative(pid.derivative_term)

                output_variable: float = pid.output_process

                pid.add_process_output(output_variable)

                voltage_amplitude = output_variable

                # Apply new Amplitude
                generator_configs: list = [
                    SCPI.set_source_voltage_amplitude(1, voltage_amplitude)
                ]

                SCPI.exec_commands(generator, generator_configs)

                sleep(0.4)

                iteration += 1
        else:
            console.print("[SAMPLING] - Error retrieving rms_value.")

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.OFF),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)
    generator.close()

    live.stop()

    console.print(
        Panel("Generator Voltage to obtain +4dBu: {}".format(voltage_amplitude))
    )

    console.print(plot_file_path)

    sp = np.full(iteration, Vpp_4dBu_exact)

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
