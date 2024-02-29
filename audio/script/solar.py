from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self

import click
import matplotlib.pyplot as plt
import numpy as np
import pyvisa
import serial
from audio.console import console
from audio.device.extech import ExtechLightMeter
from audio.math import percentage_error
from audio.math.pid import PidController, TimedValue
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from pyvisa.resources.tcpip import TCPIPInstrument
from rich.live import Live
from rich.prompt import Prompt
from rich.table import Column, Table


@dataclass()
class PanelCharacterizationData:
    lux: float | None
    open_voltage: float | None
    mppt_voltage: float | None
    mppt_current: float | None
    mppt_power: float | None
    mppt_voltage_percentage: float | None
    mppt_voc: float | None


@dataclass()
class PanelCharacterizationSweepData:
    voltage_set: float | None
    voltage_read: float | None
    current: float | None
    power: float | None
    voltage_percentage: float | None


class PanelCharacterizationSweepTable:
    _table: Table

    def __init__(self: Self) -> None:
        self._table = Table(
            Column(r"Voltage Set \[V]", justify="right"),
            Column(r"Voltage Read \[V]", justify="right"),
            Column(r"Current \[mA]", justify="right"),
            Column(r"Power \[mW]", justify="right"),
            Column(r"Voltage Percentage [%]", justify="right"),
            title="Solar Panel Characterization Sweep",
        )

    def add_row(
        self: Self,
        panel_characterization_data: PanelCharacterizationSweepData,
    ) -> Self:
        self._table.add_row(
            f"{panel_characterization_data.voltage_set:.5f}",
            f"{panel_characterization_data.voltage_read:.5f}",
            f"{panel_characterization_data.current:.5f}",
            f"{panel_characterization_data.power:.5}",
            f"{panel_characterization_data.voltage_percentage:3.2%}",
        )
        return self

    @property
    def table(self: Self) -> Table:
        return self._table


numErrors = 0


@dataclass()
class PanelCharacterizationTable:
    _table: Table

    def __init__(self: Self) -> None:
        self._table = Table(
            Column(r"Lux [lx]", justify="right"),
            Column(r"Open Voltage \[V]", justify="right"),
            Column(r"MPPT Voltage \[V]", justify="right"),
            Column(r"MPPT Current \[mA]", justify="right"),
            Column(r"MPPT Power \[mW]", justify="right"),
            Column(r"MPPT Voltage Percentage [%]", justify="right"),
            title="Solar Panel Characterization",
        )

    def add_row(
        self: Self,
        panel_characterization_data: PanelCharacterizationData,
    ) -> Self:
        self._table.add_row(
            f"{panel_characterization_data.lux: 5.1f}",
            f"{panel_characterization_data.open_voltage:.5f}",
            f"{panel_characterization_data.mppt_voltage:.5f}",
            f"{panel_characterization_data.mppt_current:.5f}",
            f"{panel_characterization_data.mppt_power:.5f}",
            f"{panel_characterization_data.mppt_voltage_percentage:3.2%}",
        )
        return self

    @property
    def table(self: Self) -> Table:
        return self._table


@click.command()
@click.option("--n_points", type=int, default=10)
def solar(
    n_points: int,
) -> None:
    title: str = Prompt.ask("Title")
    rm = pyvisa.ResourceManager()
    resource: TCPIPInstrument = rm.open_resource("TCPIP0::192.168.10.233::inst0::INSTR")
    resource.read_termination = "\n"

    table = Table(
        Column("Voltage Set", justify="right"),
        Column("Voltage Read", justify="right"),
        Column("Current", justify="right"),
        Column("Power", justify="right"),
        Column("Percentage", justify="right"),
        title="Solar Panel Characterization",
    )

    resource.write("*IDN?")
    response: str = resource.read(encoding="utf-8")
    console.print(response)

    resource.write("OUTPut:MODE SINK")

    resource.write("MEAS:VOLT:DVM?")
    voltage_dvm = float(resource.read(encoding="utf-8"))
    console.print("VOLT:DVM", f"{voltage_dvm:f}")

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
        vertical_overflow="crop",
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
        x_voltage,
        y_power,
        color="blue",
        label=f"MAX Power: {max_power:0.6f} mW",
    )
    axs[2].axvline(max_power_percentage, linestyle="--", color="black")
    for ax in axs:
        ax.legend(loc="best")
        ax.grid(visible=True, which="both", axis="both")
    plt.show()
    plt.close()


class RohdeSchwarzNGU201:
    _device: TCPIPInstrument

    def __init__(self: Self, resource_name: str) -> None:
        rm = pyvisa.ResourceManager()
        console.print(rm.list_resources())
        self._device = rm.open_resource(resource_name)
        self._device.read_termination = "\n"

    def identify(self: Self) -> str:
        self._device.write("*IDN?")
        return self._device.read(encoding="utf-8")

    def voltage_dvm_enable(self: Self) -> None:
        self._device.write("SOURce:VOLTage:DVM:STATe 1")

    def output_mode_sink(self: Self) -> None:
        self._device.write("OUTPut:MODE SINK")

    def measure_voltage_dvm(self: Self) -> float:
        self._device.write("MEAS:VOLT:DVM?")
        return float(self._device.read(encoding="utf-8"))

    def output_state_on(self: Self) -> None:
        self._device.write("OUTPut:STATe 1")

    def output_state_off(self: Self) -> None:
        self._device.write("OUTPut:STATe 0")

    def system_local(self: Self) -> None:
        self._device.write("SYSTem:LOCal")

    def system_remote(self: Self) -> None:
        self._device.write("SYSTem:REMote")

    def source_voltage_set(self: Self, voltage: float) -> None:
        self._device.write(f"SOURce:VOLTage {voltage}")

    def measure_voltage(self: Self) -> float:
        self._device.write("MEASure:VOLTage?")
        return float(self._device.read(encoding="utf-8"))

    def measure_current(self: Self) -> float:
        self._device.write("MEASure:CURRent?")
        return float(self._device.read(encoding="utf-8"))

    def measure_power(self: Self) -> float:
        self._device.write("MEASure:POWer?")
        return float(self._device.read(encoding="utf-8"))

    def reset(self: Self) -> None:
        self._device.write("*RST")

    def source_resistance_state_on(self: Self) -> None:
        self._device.write("SOURce:RESistance:STATe 1")

    def source_resistance_state_off(self: Self) -> None:
        self._device.write("SOURce:RESistance:STATe 0")

    def source_resistance_set(self: Self, resistance: float) -> None:
        self._device.write(f"SOURce:RESistance {resistance}")


def solar_find_max_power(
    rohde: RohdeSchwarzNGU201,
    n_points: int,
    *,
    show_graph: bool = False,
    lux: int | None = None,
    output_graph_folder: Path | None = None,
) -> PanelCharacterizationData:
    solar_panel_sweep_table = PanelCharacterizationSweepTable()
    console.log(rohde.identify())

    rohde.voltage_dvm_enable()
    rohde.output_mode_sink()

    time.sleep(1)

    voltage_dvm: float = rohde.measure_voltage_dvm()
    console.log("VOLT:DVM", f"{voltage_dvm:f}")

    rohde.output_state_on()

    time.sleep(0.5)

    x_voltage: list[float] = []
    y_voltage: list[float] = []
    y_current: list[float] = []
    y_power: list[float] = []
    x_voltage_percentage: list[float] = []

    voltage_range = np.linspace(
        voltage_dvm * 0.5,
        voltage_dvm * 0.99,
        n_points,
        endpoint=True,
    )
    rohde.source_voltage_set(voltage_range[0])

    time.sleep(0.5)

    #    with Live(
    #        solar_panel_sweep_table.table,
    #        console=console,
    #        vertical_overflow="crop",
    #        screen=True,
    #    ):
    for voltage_set in voltage_range:
        x_voltage.append(voltage_set)
        #        time.sleep(0.03)
        #        rohde.source_voltage_set(voltage_set)

        console.print(".", end="")
        measures_ok: bool = False
        while not measures_ok:
            rohde.source_voltage_set(voltage_set)
            time.sleep(0.3)
            voltage_read: float = rohde.measure_voltage()
            #            console.print(",", end="")
            time.sleep(0.01)
            current: float = -rohde.measure_current() * 1000
            #            console.print(":", end="")
            time.sleep(0.01)
            power: float = -rohde.measure_power() * 1000
            #            console.print(";", end="")
            #            console.print(voltage_read, current, power)
            if current < 0:
                console.print("Current < 0!", current, end="")
            if power < 0:
                console.print("Power < 0!", power, end="")
            if power > 0 and current > 0:
                measures_ok = True
            else:
                console.print(" Ancora Errore!", end="")
                numErrors = numErrors + 1

        y_voltage.append(voltage_read)
        #        time.sleep(0.03)
        y_current.append(current)
        #        time.sleep(0.03)
        y_power.append(power)

        voltage_percentage: float = voltage_set / voltage_dvm
        #        time.sleep(0.03)
        x_voltage_percentage.append(voltage_percentage)
        #        time.sleep(0.03)

        panel_characterization_sweep_data = PanelCharacterizationSweepData(
            voltage_set=voltage_set,
            voltage_read=voltage_read,
            current=current,
            power=power,
            voltage_percentage=voltage_percentage,
        )
        time.sleep(0.03)
        solar_panel_sweep_table.add_row(panel_characterization_sweep_data)

    rohde.output_state_off()
    rohde.system_local()

    console.print(solar_panel_sweep_table.table)

    _max_power: float = -10
    _max_p_index: int = 0
    for idx, p in enumerate(y_power):
        if p > _max_power:
            _max_power = p
            _max_p_index = idx

    mppt_voltage: float = y_voltage[_max_p_index]
    mppt_current: float = y_current[_max_p_index]
    mppt_power: float = _max_power
    mppt_voltage_percentage: float = voltage_range[_max_p_index] / voltage_dvm

    panel_characterization = PanelCharacterizationData(
        lux=lux,
        open_voltage=voltage_dvm,
        mppt_voltage=mppt_voltage,
        mppt_current=mppt_current,
        mppt_power=mppt_power,
        mppt_voltage_percentage=mppt_voltage_percentage,
        mppt_voc=voltage_dvm,
    )

    solar_graph(
        title="Solar Max Power{}".format(
            f" [lux: {lux}]" if lux is not None else "",
        ),
        voltage_dvm=voltage_dvm,
        x_voltage=x_voltage,
        y_voltage=y_voltage,
        max_power_percentage=mppt_voltage_percentage,
        y_current=y_current,
        y_power=y_power,
        max_power=_max_power,
        output_graph_folder=output_graph_folder,
        show_graph=show_graph,
    )

    return panel_characterization


def solar_graph(
    title: str,
    voltage_dvm: float,
    x_voltage: list[float],
    y_voltage: list[float],
    max_power_percentage: float,
    y_current: list[float],
    y_power: list[float],
    max_power: float,
    *,
    output_graph_folder: Path | None = None,
    show_graph: bool = False,
) -> None:
    fig, axs = plt.subplots(3, figsize=(16, 8), dpi=300)
    fig.suptitle(title + f" [Open Voltage:{voltage_dvm}]")

    x_voltage = [(v / voltage_dvm) * 100 for v in x_voltage]

    axs[0].plot(
        x_voltage,
        y_voltage,
        color="green",
        label=f"V - MAX Percentage: {max_power_percentage:0.1%}%",
    )
    axs[0].axvline(max_power_percentage * 100, linestyle="--", color="black")

    axs[1].plot(x_voltage, y_current, color="red", label="Current [mA]")
    axs[1].axvline(max_power_percentage * 100, linestyle="--", color="black")

    axs[2].plot(
        x_voltage,
        y_power,
        color="blue",
        label=f"P - MAX Power: {max_power:0.6f} mW",
    )
    axs[2].axvline(max_power_percentage * 100, linestyle="--", color="black")

    for ax in axs:
        ax.legend(loc="best")
        ax.grid(visible=True, which="both", axis="both")

    if output_graph_folder is not None:
        fig.savefig(output_graph_folder)

    if show_graph:
        plt.show()

    plt.close()


@click.command()
def lux() -> None:
    lux_meter = ExtechLightMeter(device_port="/dev/ttyUSB0")
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
    voltage_start = 38.0
    korad = KoradPowerSupplyKA6003P(
        device_port="/dev/ttyACM0",
        voltage_max=48,
        current_max=1.4,
        time_delay=0.5,
    )
    lux_meter = ExtechLightMeter(device_port="/dev/ttyUSB0")
    pid = PidController(
        lux,
        controller_gain=0.0025,
        tau_integral=0.5,
        tau_derivative=0.015,
        controller_output_zero=voltage_start,
    )
    lux_pid(pid, korad, lux_meter, lux, voltage_start, other_screen=False)


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


def lux_pid(
    pid: PidController,
    korad: KoradPowerSupplyKA6003P,
    lux_meter: ExtechLightMeter,
    target_lux: int,
    voltage_start: float,
    *,
    other_screen: bool = True,
    max_delta_lux: int = 2,
) -> float:
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

    live = Live(
        table,
        vertical_overflow="visible",
        screen=other_screen,
    )

    korad.set_current(1.3)
    korad.set_voltage(voltage_start)
    korad.power_on()

    output_voltage: float = voltage_start

    lux_found: bool = False
    iteration: int = 0
    # live.start()
    while not lux_found:
        time.sleep(0.2)
        console.print(".", end="")
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


@dataclass()
class CustomPidData:
    interation: int
    voltage_set: int
    target_lux: int
    lux_read: int
    error: int


class CustomPidTable:
    _table: Table

    def __init__(self: Self) -> None:
        self._table = Table(
            Column(r"Iteration", justify="right"),
            Column(r"Voltage Set [mV]", justify="right"),
            Column(r"Lux Target [lx]", justify="right"),
            Column(r"Lux Read [lx]", justify="right"),
            Column(r"error [lx]", justify="right"),
            title="Solar Panel Characterization Sweep",
        )

    def add_row(
        self: Self,
        data: CustomPidData,
    ) -> Self:
        self._table.add_row(
            f"{data.interation: 3d}",
            f"{data.voltage_set:2.2f}",
            f"{data.target_lux:3d}",
            f"{data.lux_read:3d}",
            f"{data.error:+3d}",
        )
        return self

    @property
    def table(self: Self) -> Table:
        return self._table


def lux_pid_custom(
    target_lux: int,
    max_delta_error_lux: int,
    voltage_start: int,
) -> None:
    korad = KoradPowerSupplyKA6003P(
        device_port="/dev/ttyACM0",
        voltage_max=48,
        current_max=1.2,
        time_delay=1,
    )
    lux_meter = ExtechLightMeter(device_port="/dev/ttyUSB0")

    voltage_set: int = voltage_start
    korad.set_current(1.2)
    korad.set_voltage(voltage_start / 100)
    korad.power_on()

    lux_found: bool = False
    _lux_apply_lux_list: list[int] = [50, 10, 5, 1]
    _lux_apply_lux_index: int = 0

    last_lux: int = 0
    iteration: int = 0

    custom_pid_table = CustomPidTable()
    live = Live(custom_pid_table.table, console=console)
    live.start()

    lux_read: int = 0

    while not lux_found:
        while True:
            try:
                lux_read = lux_meter.read()
            except Exception:
                console.log("[ERROR]: lux_read invalid")
            else:
                break

        error: int = target_lux - lux_read

        custom_pid_data = CustomPidData(
            interation=iteration,
            voltage_set=voltage_set,
            target_lux=target_lux,
            lux_read=lux_read,
            error=error,
        )

        custom_pid_table.add_row(custom_pid_data)

        if abs(error) <= max_delta_error_lux:
            lux_found = True
            break

        last_error: int = target_lux - last_lux

        if last_error * error < 0:
            _lux_apply_lux_index = min(
                _lux_apply_lux_index + 1,
                len(_lux_apply_lux_list) - 1,
            )

        voltage_set += _lux_apply_lux_list[_lux_apply_lux_index] * int(
            abs(error) / error,
        )
        last_lux = lux_read
        korad.set_voltage(voltage_set / 100)
        iteration += 1

    live.stop()
    console.print(custom_pid_table.table)
    console.log("LUX FOUND", lux_read)


@click.command()
@click.option("--lux", type=int)
@click.option("--n_points_sweep", type=int, default=20)
@click.option("--show_graphs", is_flag=True)
def find_max_power(
    lux: int,
    n_points_sweep: int,
    *,
    show_graphs: bool,
) -> None:
    rohde = RohdeSchwarzNGU201("TCPIP0::192.168.10.233::inst0::INSTR")
    panel_characterization: PanelCharacterizationData = solar_find_max_power(
        rohde,
        n_points_sweep,
        show_graph=show_graphs,
    )
    panel_characterization.lux = lux

    console.print(
        PanelCharacterizationTable().add_row(panel_characterization).table,
    )
    _max_power: float = panel_characterization.mppt_power
    _mppt_percentage: float = panel_characterization.mppt_voltage_percentage

    console.log("MAX POWER: ", _max_power)
    console.log("MAX PERCENTAGE: ", _mppt_percentage)


@click.command()
@click.option(
    "--min_lux",
    type=int,
    default=20,
    help="Minimum Measure Lux Value",
)
@click.option(
    "--max_lux",
    type=int,
    default=1000,
    help="maximum Measure Lux Value",
)
@click.option("--n_points", type=int, default=10)
@click.option(
    "--n_points_mppt",
    type=int,
    default=20,
    help="Number of Sweep points for MPPT (Maximum Power Point Tracking)",
)
@click.option("--show_graphs", is_flag=True)
def panel_characterization(
    min_lux: int,
    max_lux: int,
    n_points: int,
    n_points_mppt: int,
    *,
    show_graphs: bool,
) -> None:
    title: str = Prompt.ask("Enter the title for the graph")

    date_now: str = datetime.now().strftime("[%Y-%m-%d %H-%M-%S]")

    folder_name: Path = Path(f"{date_now} {title}")

    lux_range = np.linspace(start=min_lux, stop=max_lux, num=n_points, endpoint=True)

    console.print("Folder:", folder_name.as_posix())
    console.print("min_lux:", min_lux)
    console.print("max_lux:", max_lux)
    console.print("n_points:", n_points)
    console.print("lux_range:", lux_range)

    folder_name.mkdir(parents=True, exist_ok=True)

    x_lux: list[float] = lux_range.tolist()
    y_max_power: list[float] = []
    z_mppt_percentage: list[float] = []
    w_mppt_voc: list[float] = []

    panel_characterization_table = PanelCharacterizationTable()

    voltage_start: int = 38

    korad = KoradPowerSupplyKA6003P(
        device_port="/dev/ttyACM0",
        voltage_max=48.5,
        current_max=1.3,
        time_delay=1,
    )
    lux_meter = ExtechLightMeter(device_port="/dev/ttyUSB0")
    rohde = RohdeSchwarzNGU201("TCPIP0::192.168.10.233::inst0::INSTR")

    for lux in lux_range:
        target_lux = int(lux)
        pid = PidController(
            target_lux,
            controller_gain=0.0045,
            tau_integral=0.5,
            tau_derivative=0.02,
            controller_output_zero=voltage_start,
        )
        lux_pid(pid, korad, lux_meter, target_lux, voltage_start, max_delta_lux=2)

        panel_characterization: PanelCharacterizationData = solar_find_max_power(
            rohde,
            n_points_mppt,
            show_graph=show_graphs,
            lux=lux,
            output_graph_folder=folder_name / f"{title} - {target_lux} Lux.png",
        )
        panel_characterization.lux = lux
        w_mppt_voc.append(panel_characterization.mppt_voc)

        console.print(
            PanelCharacterizationTable().add_row(panel_characterization).table,
        )
        _max_power: float = panel_characterization.mppt_power
        _mppt_percentage: float = panel_characterization.mppt_voltage_percentage

        y_max_power.append(_max_power)
        z_mppt_percentage.append(_mppt_percentage)

        panel_characterization_table.add_row(panel_characterization)

    console.print(panel_characterization_table.table)
    console.print("number of NGU201 Errors = ", numErrors)

    korad.power_off()

    panel_characterization_graph(
        title=title,
        x_lux=x_lux,
        y_max_power=y_max_power,
        z_mppt_percentage=z_mppt_percentage,
        w_mppt_voc=w_mppt_voc,
        output_graph_folder=folder_name / f"{title}.png",
    )


def panel_characterization_graph(
    title: str,
    x_lux: list[float],
    y_max_power: list[float],
    z_mppt_percentage: list[float],
    w_mppt_voc: list[float],
    *,
    output_graph_folder: Path | None = None,
    show_graph: bool = False,
) -> None:
    plt.close("all")

    sub_plot: tuple[Figure, Axes] = plt.subplots(1, figsize=(16, 8), dpi=300)
    fig, graph = sub_plot
    fig.suptitle(title)

    graph.plot(x_lux, y_max_power, ".-")

    for lux, power, percentage_voltage, mppt_voc in zip(
        x_lux,
        y_max_power,
        z_mppt_percentage,
        w_mppt_voc,
        strict=True,
    ):
        graph.annotate(
            f"({lux:.0f} lux, {power:.3f} mW, {percentage_voltage:.1%} VOC [{mppt_voc:.3f}])",
            xy=(lux, power),
            textcoords="offset points",  # how to position the text
            xytext=(0, 10),  # distance from text to points (x,y)
            ha="center",  # horizontal alignment can be left, right or center
        )

    if output_graph_folder is not None:
        fig.savefig(output_graph_folder)

    if show_graph:
        plt.show()
