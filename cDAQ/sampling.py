import math
from pathlib import Path
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
from rich.table import Column, Table
from usbtmc import Instrument
from cDAQ.math.pid import PID

import cDAQ.ui.terminal as ui_t
from cDAQ.alghorithm import LogaritmicScale
from cDAQ.config import Config, Plot
from cDAQ.config.type import ModAuto
from cDAQ.console import console
from cDAQ.math import INTERPOLATION_KIND, logx_interpolation_model, unit_normalization
from cDAQ.scpi import SCPI, Bandwidth, Switch
from cDAQ.timer import Timer, Timer_Message
from cDAQ.usbtmc import UsbTmc, get_device_list, print_devices_list
from cDAQ.utility import RMS, percentage_error, transfer_function


def sampling_curve(
    config: Config,
    measurements_file_path: Path,
    debug: bool = False,
):

    live_group = Group(
        Panel(Group(ui_t.progress_list_task, ui_t.progress_sweep, ui_t.progress_task)),
    )
    live = Live(
        live_group,
        transient=True,
        console=console,
    )
    live.start()

    task_sampling = ui_t.progress_list_task.add_task(
        "Sampling", start=False, task="Retriving Devices"
    )
    ui_t.progress_list_task.start_task(task_sampling)

    # Asks for the 2 instruments
    list_devices: List[Instrument] = get_device_list()
    if debug:
        print_devices_list(list_devices)

    generator: UsbTmc = UsbTmc(list_devices[0])

    ui_t.progress_list_task.update(task_sampling, task="Setting Devices")

    # Open the Instruments interfaces
    # Auto Close with the destructor
    generator.open()

    # Sets the Configuration for the Voltmeter
    generator_configs: list = [
        SCPI.clear(),
        # SCPI.reset(),
        SCPI.set_output(1, Switch.OFF),
        SCPI.set_function_voltage_ac(),
        SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
        SCPI.set_source_voltage_amplitude(1, round(config.rigol.amplitude_pp, 5)),
        SCPI.set_source_frequency(1, round(config.sampling.f_range.min, 5)),
    ]

    SCPI.exec_commands(generator, generator_configs)

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    log_scale: LogaritmicScale = LogaritmicScale(
        config.sampling.f_range.min,
        config.sampling.f_range.max,
        config.sampling.points_per_decade,
    )

    f = open(measurements_file_path, "w")
    f.write("{},{},{}\n".format("Frequency", "RMS Value", "dbV"))

    frequency: float = round(config.sampling.f_range.min, 5)

    table = Table(
        Column("Frequency [Hz]", justify="right"),
        Column("Fs [Hz]", justify="right"),
        Column("Number of samples", justify="right"),
        Column("Rms Value [V]", justify="right"),
        Column("Gain \[dB]", justify="right"),
        Column("Time \[s]", justify="right"),
        title="[blue]Sweep.",
    )

    max_dB: Optional[float] = None
    ui_t.progress_list_task.update(task_sampling, task="Sweep")

    task_sweep = ui_t.progress_sweep.add_task(
        "Sweep", start=False, total=len(log_scale.f_list)
    )
    ui_t.progress_sweep.start_task(task_sweep)

    for frequency in log_scale.f_list:

        ui_t.progress_sweep.update(task_sweep, frequency=round(frequency, 5))

        # Sets the Frequency
        generator.write(SCPI.set_source_frequency(1, round(frequency, 5)))

        Fs = config.nidaq._max_Fs

        if frequency < 20:
            Fs = frequency * config.sampling.n_fs
            config.sampling.number_of_samples = 90
        elif frequency <= 1000:
            Fs = frequency * config.sampling.n_fs
        elif frequency <= 10000:
            Fs = frequency * config.sampling.n_fs

        if Fs > config.nidaq.max_Fs:
            Fs = config.nidaq.max_Fs

        time = Timer()
        time.start()

        # GET MEASUREMENTS
        rms_value: Optional[float] = RMS.rms(
            frequency=frequency,
            Fs=Fs,
            ch_input=config.nidaq.ch_input,
            max_voltage=config.nidaq.max_voltage,
            min_voltage=config.nidaq.min_voltage,
            number_of_samples=config.sampling.number_of_samples,
            time_report=False,
        )

        message: Timer_Message = time.stop()

        if rms_value:

            perc_error = percentage_error(
                exact=(config.rigol.amplitude_pp / 2) / np.math.sqrt(2),
                approx=rms_value,
            )

            gain_bBV: float = 20 * np.log10(
                rms_value * 2 * np.math.sqrt(2) / config.rigol.amplitude_pp
            )

            transfer_func_dB = transfer_function(
                rms_value, config.rigol.amplitude_pp / (2 * np.math.sqrt(2))
            )

            if max_dB:
                max_dB = max(abs(max_dB), abs(transfer_func_dB))
            else:
                max_dB = transfer_func_dB

            table.add_row(
                "{:.2f}".format(frequency),
                "{:.2f}".format(Fs),
                "{}".format(config.sampling.number_of_samples),
                "{:.5f} ".format(round(rms_value, 5)),
                "[{}]{:.2f}[/]".format(
                    "red" if gain_bBV <= 0 else "green", transfer_func_dB
                ),
                "[cyan]{}[/]".format(message.elapsed_time),
            )

            """File Writing"""
            f.write(
                "{},{},{}\n".format(
                    frequency,
                    rms_value,
                    gain_bBV,
                )
            )

            ui_t.progress_sweep.update(task_sweep, advance=1)

        else:
            console.print("[ERROR] - Error retriving rms_value.", style="error")

    if debug:
        console.print(table)

    ui_t.progress_sweep.remove_task(task_sweep)

    f.close()

    ui_t.progress_list_task.update(task_sampling, task="Shutting down the Channel 1")

    SCPI.exec_commands(
        generator,
        [
            SCPI.set_output(1, Switch.OFF),
            SCPI.clear(),
        ],
    )

    ui_t.progress_list_task.remove_task(task_sampling)

    if debug:
        console.print(Panel("max_dB: {}".format(max_dB)))

    console.print(
        Panel(
            '[bold][[blue]FILE[/blue] - [cyan]CSV[/cyan]][/bold] - "[bold green]{}[/bold green]"'.format(
                measurements_file_path.absolute().resolve()
            )
        )
    )

    live.stop()


def plot_from_csv(
    measurements_file_path: Path,
    plot_file_path: Path,
    plot_config: Plot,
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

    if debug:
        console.print(Panel(plot_config.tree(), title="Plot Configurations"))

    x_frequency: List[float] = []
    y_dBV: List[float] = []

    ui_t.progress_list_task.update(task_plotting, task="Read Measurements")

    measurements = pd.read_csv(
        measurements_file_path, header=0, names=["Frequency", "RMS Value", "dbV"]
    )

    for i, row in measurements.iterrows():
        y_dBV.append(row["dbV"])
        x_frequency.append(row["Frequency"])

    if debug:
        console.print(
            Panel(
                "min dB: {}\n".format(min(y_dBV))
                + "max dB: {}\n".format(max(y_dBV))
                + "diff dB: {}".format(abs(max(y_dBV) - min(y_dBV)))
            )
        )

    ui_t.progress_list_task.update(task_plotting, task="Apply Offset")

    y_offset: Optional[float] = None
    if plot_config.y_offset:
        if isinstance(plot_config.y_offset, float):
            y_offset = plot_config.y_offset
        elif isinstance(plot_config.y_offset, ModAuto):
            if plot_config.y_offset == ModAuto.MIN:
                y_offset = float(min(y_dBV))
            elif plot_config.y_offset == ModAuto.MAX:
                y_offset = float(max(y_dBV))
            elif plot_config.y_offset == ModAuto.NO:
                y_offset = None
            else:
                console.print('y_offset should be "max", "min" or "no".', style="error")

        if y_offset:
            for i in range(len(y_dBV)):
                y_dBV[i] = y_dBV[i] - y_offset

    ui_t.progress_list_task.update(task_plotting, task="Interpolate")

    plot: Tuple[Figure, Axes] = plt.subplots(figsize=(16 * 2, 9 * 2), dpi=600)

    fig: Figure
    axes: Axes

    fig, axes = plot

    x_interpolated, y_interpolated = logx_interpolation_model(
        x_frequency,
        y_dBV,
        int(len(x_frequency) * 5),
        kind=INTERPOLATION_KIND.CUBIC,
    )

    xy_sampled = [x_frequency, y_dBV, "o"]
    xy_interpolated = [x_interpolated, y_interpolated, "-"]

    ui_t.progress_list_task.update(task_plotting, task="Plotting Graph")

    axes.semilogx(
        *xy_sampled,
        *xy_interpolated,
        linewidth=4,
    )
    # Added Line to y = 3
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
            round(y_offset, 5) if y_offset else 0
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

    if plot_config.y_limit:
        axes.set_ylim(plot_config.y_limit.min, plot_config.y_limit.max)
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


def config_offset(
    config: Config,
    # measurements_file_path: Path,
    debug: bool = False,
):

    voltage_amplitude_start: float = 0.2
    voltage_amplitude = voltage_amplitude_start
    frequency = 1000
    Fs = frequency * config.sampling.n_fs
    diff_voltage = 0.001
    Vpp_4dBu_exact = 1.227653
    step_voltage = 0.2

    table = Table(
        Column("4dBu [V]", justify="right"),
        Column("Vpp [V]", justify="right"),
        Column("Rms Value [V]", justify="right"),
        Column("Diff Vpp [V]", justify="right"),
        Column("Error [%]", justify="right"),
        Column("Found", justify="center"),
        Column("Count", justify="right"),
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
    )
    live.start()

    task_sampling = ui_t.progress_list_task.add_task(
        "CONFIGURING", start=False, task="Retriving Devices"
    )
    ui_t.progress_list_task.start_task(task_sampling)

    # Asks for the 2 instruments
    list_devices: List[Instrument] = get_device_list()
    if debug:
        print_devices_list(list_devices)

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
        SCPI.set_source_voltage_amplitude(1, voltage_amplitude_start),
        SCPI.set_source_frequency(1, frequency),
    ]

    SCPI.exec_commands(generator, generator_configs)

    generator_ac_curves: List[str] = [
        SCPI.set_output(1, Switch.ON),
    ]

    SCPI.exec_commands(generator, generator_ac_curves)

    ui_t.progress_list_task.update(task_sampling, task="Setting Devices")

    Vpp_found: bool = False
    iteration: int = 0
    iteration_max = 40

    ui_t.progress_list_task.update(task_sampling, task="Searching for Voltage offset")

    error: float = 0.0
    error_prev: float = 0.0

    pid = PID(
        step=np.full(40, 1.27),
        controller_gain=15.0,
        tauI=2.0,
        tauD=1.0,
        controller_output_zero=0.0,
    )

    while not Vpp_found:

        # GET MEASUREMENTS
        rms_value: Optional[float] = RMS.rms(
            frequency=frequency,
            Fs=Fs,
            ch_input=config.nidaq.ch_input,
            max_voltage=config.nidaq.max_voltage,
            min_voltage=config.nidaq.min_voltage,
            number_of_samples=config.sampling.number_of_samples,
            time_report=False,
        )

        if rms_value:
            error = Vpp_4dBu_exact - rms_value
            diff = Vpp_4dBu_exact - rms_value

            output_process = pid.controller_output_zero + pid.controller_gain

            error_percentage = percentage_error(exact=Vpp_4dBu_exact, approx=rms_value)

            if np.abs(diff) > diff_voltage:
                voltage_amplitude = voltage_amplitude - unit_normalization(
                    error_percentage
                ) * diff * (step_voltage - step_voltage * (iteration / iteration_max))

                # Apply new Amplitude
                generator_configs: list = [
                    SCPI.set_source_voltage_amplitude(1, voltage_amplitude),
                ]

                SCPI.exec_commands(generator, generator_configs)
            else:
                if iteration > iteration_max - 1:
                    Vpp_found = True
                iteration = iteration + 1

            table.add_row(
                "{:.8f}".format(Vpp_4dBu_exact),
                "{:.8f}".format(voltage_amplitude),
                "{:.8f}".format(rms_value),
                "{:.8f} ".format(diff),
                "[{}]{:.5f}[/]".format(
                    "red" if error_percentage <= 0 else "green", error_percentage
                ),
                "{}".format(Vpp_found),
                "{}".format(iteration),
            )

        else:
            console.print("[SAMPLING] - Error retriving rms_value.")

    live.stop()

    console.print(Panel("Voltage Offset: {}".format(voltage_amplitude)))
