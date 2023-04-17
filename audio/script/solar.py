from __future__ import annotations

import sys
import time
from typing import Self

import click
import matplotlib.pyplot as plt
import numpy as np
import pyvisa
import serial
from extech.light_meter import LightMeter
from pyvisa.resources.tcpip import TCPIPInstrument
from rich.live import Live
from rich.prompt import Prompt
from rich.table import Table

from audio.console import console
from audio.math import percentage_error
from audio.math.pid import PidController, TimedValue


@click.command()
@click.option("--n_points", type=int, default=10)
def solar(
    n_points: int,
) -> None:
    title = Prompt.ask("Title")
    rm = pyvisa.ResourceManager()
    resource: TCPIPInstrument = rm.open_resource("TCPIP0::192.168.10.233::inst0::INSTR")
    resource.read_termination = "\n"

    from rich.table import Column

    table = Table(
        Column("Voltage Set", justify="right"),
        Column("Voltage Read", justify="right"),
        Column("Current", justify="right"),
        Column("Power", justify="right"),
        Column("Percentage", justify="right"),
        title="Solar Panel Characterization",
    )

    resource.write("*IDN?")
    response = resource.read(encoding="utf-8")
    console.print(response)

    # resource.write("*RST")
    # resource.write("SOURce:RESistance:STATe 1")
    # resource.write("SOURce:RESistance 10000")
    resource.write("OUTPut:MODE SINK")
    import time

    resource.write("MEAS:VOLT:DVM? (@1)")
    voltage_dvm = float(resource.read(encoding="utf-8"))
    console.print("VOLT:DVM", f"{voltage_dvm:f}")

    # time.sleep(5)

    resource.write("OUTPut:STATe 1")

    time.sleep(0.2)

    x_voltage: list[float] = []
    y_voltage: list[float] = []
    y_current: list[float] = []
    y_power: list[float] = []
    y_percentage: list[float] = []

    voltage_range = np.linspace(
        voltage_dvm / 2,
        (voltage_dvm) * 0.99,
        n_points,
        endpoint=True,
    )
    resource.write(f"SOURce:VOLTage {voltage_range[0]}")

    time.sleep(0.5)

    with Live(
        table,
        console=console,
        vertical_overflow="visible",
    ):
        for set_voltage in voltage_range:
            x_voltage.append(set_voltage)
            resource.write(f"SOURce:VOLTage {set_voltage}")
            time.sleep(1)

            resource.write("MEASure:VOLTage?")
            voltage = float(resource.read(encoding="utf-8"))
            y_voltage.append(voltage)

            resource.write("MEASure:CURRent?")
            current = -float(resource.read(encoding="utf-8"))
            current *= 1000
            y_current.append(current)

            resource.write("MEASure:POWer?")
            power = -float(resource.read(encoding="utf-8"))
            power *= 1000
            y_power.append(power)

            percentage = (set_voltage / voltage_dvm) * 100
            y_percentage.append(percentage)
            table.add_row(
                f"{set_voltage:0.4f}",
                f"{voltage:0.4f}",
                f"{current:0.4f}",
                f"{power:0.6f}",
                f"{percentage:0.1f}%",
            )

    resource.write("OUTPut:STATe 0")
    resource.write("SYSTem:LOCal")
    # resource.write("SYSTem:REMote")

    max_power: float = -10
    max_p_index: int = 0
    for idx, p in enumerate(y_power):
        if p > max_power:
            max_power = p
            max_p_index = idx

    max_power_percentage = y_percentage[max_p_index]

    console.print("MAX Power", max_power)
    console.print("MAX Power Voltage", y_voltage[max_p_index])
    console.print("MAX Power Current", y_current[max_p_index])

    fig, axs = plt.subplots(3)
    fig.suptitle(title + f" [Open Voltage:{voltage_dvm}]")

    x_voltage = [(v / voltage_dvm) * 100 for v in x_voltage]

    axs[0].plot(
        x_voltage,
        y_voltage,
        color="green",
        label=f"MAX Percentage: {max_power_percentage:0.1f}%",
    )
    axs[1].plot(x_voltage, y_current, color="red", label="")
    axs[2].plot(
        x_voltage, y_power, color="blue", label=f"MAX Power: {max_power:0.6f} mW"
    )
    axs[2].axvline(max_power_percentage, linestyle="--", color="black")
    for ax in axs:
        ax.legend(loc="best")
        ax.grid(visible=True, which="both", axis="both")
    plt.show()
    plt.close()


def solar_find_max_power(
    n_points: int,
    *,
    show_graph: bool = False,
) -> float:
    rm = pyvisa.ResourceManager()
    resource: TCPIPInstrument = rm.open_resource("TCPIP0::192.168.10.233::inst0::INSTR")
    resource.read_termination = "\n"

    from rich.table import Column

    table = Table(
        Column("Voltage Set", justify="right"),
        Column("Voltage Read", justify="right"),
        Column("Current", justify="right"),
        Column("Power", justify="right"),
        Column("Percentage", justify="right"),
        title="Solar Panel Characterization",
    )

    resource.write("*IDN?")
    response = resource.read(encoding="utf-8")
    console.print(response)

    # resource.write("*RST")
    # resource.write("SOURce:RESistance:STATe 1")
    # resource.write("SOURce:RESistance 10000")
    resource.write("OUTPut:MODE SINK")
    import time

    resource.write("MEAS:VOLT:DVM? (@1)")
    voltage_dvm = float(resource.read(encoding="utf-8"))
    console.print("VOLT:DVM", f"{voltage_dvm:f}")

    # time.sleep(5)

    resource.write("OUTPut:STATe 1")

    time.sleep(0.2)

    x_voltage: list[float] = []
    y_voltage: list[float] = []
    y_current: list[float] = []
    y_power: list[float] = []
    y_percentage: list[float] = []

    voltage_range = np.linspace(
        voltage_dvm / 2,
        (voltage_dvm) * 0.99,
        n_points,
        endpoint=True,
    )
    resource.write(f"SOURce:VOLTage {voltage_range[0]}")

    time.sleep(0.5)

    with Live(
        table,
        console=console,
        vertical_overflow="visible",
    ):
        for set_voltage in voltage_range:
            x_voltage.append(set_voltage)
            resource.write(f"SOURce:VOLTage {set_voltage}")
            time.sleep(1)

            resource.write("MEASure:VOLTage?")
            voltage = float(resource.read(encoding="utf-8"))
            y_voltage.append(voltage)

            resource.write("MEASure:CURRent?")
            current = -float(resource.read(encoding="utf-8"))
            current *= 1000
            y_current.append(current)

            resource.write("MEASure:POWer?")
            power = -float(resource.read(encoding="utf-8"))
            power *= 1000
            y_power.append(power)

            percentage = (set_voltage / voltage_dvm) * 100
            y_percentage.append(percentage)
            table.add_row(
                f"{set_voltage:0.4f}",
                f"{voltage:0.4f}",
                f"{current:0.4f}",
                f"{power:0.6f}",
                f"{percentage:0.1f}%",
            )

    resource.write("OUTPut:STATe 0")
    resource.write("SYSTem:LOCal")
    # resource.write("SYSTem:REMote")

    max_power: float = -10
    max_p_index: int = 0
    for idx, p in enumerate(y_power):
        if p > max_power:
            max_power = p
            max_p_index = idx

    max_power_percentage = y_percentage[max_p_index]

    console.print("MAX Power", max_power)
    console.print("MAX Power Voltage", y_voltage[max_p_index])
    console.print("MAX Power Current", y_current[max_p_index])
    console.print("MAX Power Percentage Voltage", voltage_range[max_p_index])

    if show_graph:
        solar_graph(
            title="title",
            voltage_dvm=voltage_dvm,
            x_voltage=x_voltage,
            y_voltage=y_voltage,
            max_power_percentage=max_power_percentage,
            y_current=y_current,
            y_power=y_power,
            max_power=max_power,
        )
    return max_power


def solar_graph(
    title: str,
    voltage_dvm: float,
    x_voltage: list[float],
    y_voltage: list[float],
    max_power_percentage: float,
    y_current: list[float],
    y_power: list[float],
    max_power: float,
):
    fig, axs = plt.subplots(3)
    fig.suptitle(title + f" [Open Voltage:{voltage_dvm}]")

    x_voltage = [(v / voltage_dvm) * 100 for v in x_voltage]

    axs[0].plot(
        x_voltage,
        y_voltage,
        color="green",
        label=f"MAX Percentage: {max_power_percentage:0.1f}%",
    )
    axs[1].plot(x_voltage, y_current, color="red", label="")
    axs[2].plot(
        x_voltage, y_power, color="blue", label=f"MAX Power: {max_power:0.6f} mW"
    )
    axs[2].axvline(max_power_percentage, linestyle="--", color="black")
    for ax in axs:
        ax.legend(loc="best")
        ax.grid(visible=True, which="both", axis="both")
    plt.show()
    plt.close()


@click.command()
def lux() -> None:
    lux_meter = LightMeter(device_port="/dev/ttyUSB1")
    data: int | None = lux_meter.read()
    console.log(data)


@click.command()
def lux_set() -> None:
    korad = KoradPowerSupplyKA6003P(
        device_port="/dev/ttyACM1",
        voltage_max=40,
        current_max=0.1,
        time_delay=1,
    )

    voltage_range = np.arange(36.0, 40.01, 0.5)

    korad.set_current(0.1)

    korad.set_voltage(voltage_range[0])

    query = korad.power_on()
    console.log(query)

    for voltage in voltage_range:
        query = korad.set_voltage(voltage=voltage)
        console.log(query)

    korad.power_off()


@click.command()
@click.argument("lux", type=int)
def lux_find(lux: int) -> None:
    lux_pid(lux, 38.0)


def scpi_set_voltage(voltage: float) -> str:
    return f"VSET1:{voltage:2.2f}"


def scpi_set_current(current: float) -> str:
    return f"ISET1:{current:1.3f}"


def scpi_power_on() -> str:
    return "OUT1"


def scpi_power_off() -> str:
    return "OUT0"


class KoradPowerSupplyKA6003P:
    device: serial.Serial
    voltage_max: float
    current_max: float
    time_delay: float

    def __init__(
        self: Self,
        /,
        device_port: str,  # "/dev/ttyACM1"
        voltage_max: float = 0,
        current_max: float = 0,
        time_delay: float = 0.1,
    ) -> None:
        try:
            self.device = serial.Serial(
                device_port,
                baudrate=9600,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=1,
            )
        except Exception as e:
            console.log(f"ERROR: {e}")
            sys.exit()

        if not self.device.is_open:
            try:
                self.device.open()
            except Exception:
                console.log("ERROR: Korad not opened.")

        self.voltage_max = voltage_max
        self.current_max = current_max
        self.time_delay = time_delay

    def __del__(self: Self) -> None:
        if not self.device.closed:
            self.device.close()

    def _write(self: Self, query: str) -> str:
        self.device.reset_input_buffer()
        self.device.write(query.encode())
        self.device.reset_input_buffer()
        time.sleep(self.time_delay)
        return query

    def power_on(self: Self) -> str:
        return self._write(scpi_power_on())

    def power_off(self: Self) -> str:
        return self._write(scpi_power_off())

    def set_voltage(self: Self, voltage: float) -> str:
        if voltage > self.voltage_max:
            voltage = self.voltage_max

        return self._write(scpi_set_voltage(voltage))

    def set_current(self: Self, current: float) -> str:
        if current > self.current_max:
            current = self.current_max

        return self._write(scpi_set_current(current))
        return self._write(scpi_set_current(current))
        return self._write(scpi_set_current(current))


def lux_pid(target_lux: int, voltage_start: float) -> float:
    max_delta_lux = 2

    pid = PidController(
        target_lux,
        controller_gain=0.001,
        tau_integral=1.2,
        tau_derivative=0.015,
        controller_output_zero=voltage_start,
    )

    korad = KoradPowerSupplyKA6003P(
        device_port="/dev/ttyACM0",
        voltage_max=42,
        current_max=0.1,
        time_delay=1,
    )
    lux_meter = LightMeter(device_port="/dev/ttyUSB1")

    from rich.table import Column

    table = Table(
        Column("Iteration", justify="right"),
        Column("Voltage [V]", justify="right"),
        Column("Lux [Lux]", justify="right"),
        Column("Error [delta]", justify="right"),
        Column("Proportional Term [V]", justify="right"),
        Column("Integral Term [V]", justify="right"),
        Column("Differential Term [V]", justify="right"),
        Column("Error [%]", justify="right"),
        title=f"[blue]{target_lux} Lux PID.",
    )

    live = Live(table, vertical_overflow="visible", screen=True)

    korad.set_current(0.1)
    korad.set_voltage(voltage_start)
    korad.power_on()

    output_voltage: float = voltage_start

    lux_found: bool = False
    iteration: int = 0
    live.start()
    while not lux_found:
        time.sleep(0.5)
        lux_read: int | None = lux_meter.read()
        if lux_read is None:
            live.console.log("ERROR: lux read none.")
            sys.exit()

        pid.add_process_variable(lux_read)

        error: int = target_lux - lux_read

        pid.add_error(TimedValue(error))

        lux_percentage_error: float = percentage_error(target_lux, lux_read)

        table.add_row(
            f"{iteration:3}",
            f"{output_voltage:.8f}",
            f"{lux_read:.8f}",
            "[{}]{:+.8f}[/]".format(
                "red" if error > max_delta_lux else "green",
                error,
            ),
            f"{pid.term.proportional[-1]:+.8f}",
            f"{pid.term.integral[-1]:+.8f}",
            f"{pid.term.derivative[-1]:+.8f}",
            "[{}]{:+.5%}[/]".format(
                "red" if lux_percentage_error > max_delta_lux else "green",
                lux_percentage_error,
            ),
        )

        if pid.check_limit_diff(error, max_delta_lux):
            lux_found = True
            live.console.log("FOUND", lux)
        else:
            pid.term.add_proportional(pid.proportional_term)
            pid.term.add_integral(pid.integral_term)
            pid.term.add_derivative(pid.derivative_term)

            output_voltage = pid.output_process
            korad.set_voltage(output_voltage)
            iteration += 1

    live.stop()
    console.print(table)
    return output_voltage


@click.command()
@click.option("--min_lux", type=int, default=20)
@click.option("--max_lux", type=int, default=1000)
@click.option("--n_points", type=int, default=10)
@click.option("--n_points", type=int, default=10)
@click.option("--n_points_sweep", type=int, default=20)
@click.option("--show_graphs", is_flag=True)
def panel_characterization(
    min_lux: int,
    max_lux: int,
    n_points: int,
    n_points_sweep: int,
    show_graphs: bool,
) -> None:
    title: str = Prompt.ask("Enter the title for the graph")
    lux_range = np.linspace(start=min_lux, stop=max_lux, num=n_points, endpoint=True)

    console.print("title:", title)
    console.print("min_lux:", min_lux)
    console.print("max_lux:", max_lux)
    console.print("n_points:", n_points)
    console.print("lux_range:", lux_range)

    x_lux: list[float] = lux_range.tolist()
    y_max_power: list[float] = []

    voltage_start = 38.0

    for lux in lux_range:
        voltage_start = lux_pid(lux, voltage_start)
        max_power = solar_find_max_power(n_points_sweep, show_graph=show_graphs)
        y_max_power.append(max_power)

    plt.close("all")
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    sub_plot: tuple[Figure, Axes] = plt.subplots(1)
    fig, graph = sub_plot
    fig.suptitle(title)

    graph.plot(x_lux, y_max_power, ".-")

    for x, y in zip(x_lux, y_max_power, strict=True):
        graph.annotate(
            f"({x:.0f},{y:.5f})",
            xy=(x, y),
            textcoords="offset points",  # how to position the text
            xytext=(0, 10),  # distance from text to points (x,y)
            ha="center",  # horizontal alignment can be left, right or center
        )

    plt.show()
