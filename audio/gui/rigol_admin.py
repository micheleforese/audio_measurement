from __future__ import annotations

import copy
import tkinter as tk
import tkinter.ttk as ttk
from enum import Enum, auto
from math import log10, sqrt
from time import sleep
from tkinter import BooleanVar, DoubleVar, IntVar, StringVar, Variable
from typing import List, Optional, Tuple

import click
from rich.panel import Panel
from usbtmc import Instrument

from audio.console import console
from audio.device.cDAQ import ni9223
from audio.math.rms import RMS
from audio.math.voltage import VoltageMode, Vrms_to_VdBu, Vrms_to_Vpp, voltage_converter
from audio.model.sampling import VoltageSampling
from audio.usb.usbtmc import UsbTmc
from audio.utility import trim_value
from audio.utility.scpi import SCPI, Bandwidth, Switch
from threading import Thread, Lock
from dataclasses import dataclass, field

rms_data_lock = Lock()

from typing import TypeVar, Generic

T = TypeVar("T")


class LockValue(Generic[T]):
    lock: Lock
    value: T

    def __init__(self, value: T) -> None:
        self.lock = Lock()
        self.value = value


@click.command()
def rigol_admin():
    console.log("HELLO GUI")
    rigol_admin_gui = RigolAdminGUI()
    rigol_admin_gui.start_loop()


@dataclass
class RmsDataParameters:
    frequency: LockValue[float]
    Fs_multiplier: LockValue[float]
    device: Optional[LockValue[ni9223]] = None
    gain: Optional[LockValue[ttk.Label]] = None
    phase: Optional[LockValue[ttk.Label]] = None

    lbls: List[
        Tuple[LockValue[ttk.Label], LockValue[ttk.Label], LockValue[ttk.Label]]
    ] = field(default_factory=lambda: [])


class RigolAdminGUI:

    windows: tk.Tk
    generator: UsbTmc
    device: ni9223
    b_on: bool

    channels = [
        "cDAQ9189-1CDBE0AMod5/ai1",
        "cDAQ9189-1CDBE0AMod5/ai3",
    ]

    amplitude_mode: VoltageMode
    amplitude: float
    n_sample: int
    fs_multiplier: int

    data: RmsDataParameters

    lbl_Vrms: ttk.Label
    ent_frequency: ttk.Entry
    ent_amplitude: ttk.Entry

    amplitude_mode_curr_string_var: StringVar
    amplitude_var: DoubleVar
    amplitude_multiplier_var: DoubleVar
    frequency_string_var: StringVar

    on_off_state: BooleanVar
    thread: Thread

    class Focus(Enum):
        AMPLITUDE = auto()
        FREQUENCY = auto()
        UNKNOWN = auto()

    focus: Focus

    def _ui_build(self):

        frm_app = tk.Frame(
            master=self.windows,
            borderwidth=5,
            background="yellow",
        )
        frm_app.pack(
            side=tk.TOP,
            fill=tk.BOTH,
            ipady=20,
        )

        self._ui_build_amplitude_modes(frm_app=frm_app)
        self._ui_build_amplitude(frm_app=frm_app)
        # self._ui_build_frequency(frm_app=frm_app)
        self._ui_build_read_voltage(frm_app=frm_app)
        self._ui_build_on_off(frm_app=frm_app)

    def _ui_build_amplitude_modes(self, frm_app: tk.Frame):
        frm_amplitude_modes = tk.Frame(
            master=frm_app,
            borderwidth=5,
            background="red",
        )
        lbl_amplitude_modes = ttk.Label(
            master=frm_amplitude_modes, text="Amplitude Modes:"
        )

        btn_amplitude_modes_Vpp = ttk.Button(
            master=frm_amplitude_modes,
            text=VoltageMode.Vpp.name,
            command=self._handle_amplitude_mode_Vpp,
        )
        btn_amplitude_modes_Vrms = ttk.Button(
            master=frm_amplitude_modes,
            text=VoltageMode.Vrms.name,
            command=self._handle_amplitude_mode_Vrms,
        )
        btn_amplitude_modes_VdBu = ttk.Button(
            master=frm_amplitude_modes,
            text=VoltageMode.VdBu.name,
            command=self._handle_amplitude_mode_VdBu,
        )

        frm_amplitude_modes.pack(
            side=tk.TOP,
            fill=tk.X,
            expand=True,
        )
        lbl_amplitude_modes.grid(row=0, column=0, sticky="e", ipadx=10)
        btn_amplitude_modes_Vpp.grid(row=0, column=1, ipadx=5)
        btn_amplitude_modes_Vrms.grid(row=0, column=2, ipadx=5)
        btn_amplitude_modes_VdBu.grid(row=0, column=3, ipadx=5)

    def _ui_build_amplitude(self, frm_app: tk.Frame):
        frm_amplitude = tk.Frame(
            master=frm_app,
        )

        lbl_amplitude = ttk.Label(
            master=frm_amplitude,
            text="Amplitude:",
        )
        frm_amplitude.pack(
            side=tk.TOP,
            fill=tk.X,
            expand=True,
        )
        ent_amplitude = ttk.Entry(
            master=frm_amplitude, width=15, textvariable=self.amplitude_var
        )
        self.ent_amplitude = ent_amplitude

        lbl_amplitude_mode_curr = ttk.Label(
            master=frm_amplitude,
            name="frequency_mode_curr",
            textvariable=self.amplitude_mode_curr_string_var,
        )

        lbl_amplitude.grid(row=0, column=0, sticky="e")
        ent_amplitude.grid(row=0, column=1, sticky="w")
        lbl_amplitude_mode_curr.grid(row=0, column=2)

        amplitude_steps = [1.0, 0.1, 0.01, 0.001]

        for idx, step in enumerate(amplitude_steps, start=3):
            ttk.Radiobutton(
                master=frm_amplitude,
                text=str(step),
                variable=self.amplitude_multiplier_var,
                value=step,
            ).grid(row=0, column=idx, sticky="e")

        self.amplitude_multiplier_var.set(amplitude_steps[0])

        def _handle_frm_amplitude_focus_in(event):
            console.log(f"[FOCUS IN]: frm_amplitude")
            self.focus = RigolAdminGUI.Focus.AMPLITUDE

        def _handle_frm_amplitude_focus_out(event):
            console.log(f"[FOCUS OUT]: frm_amplitude")
            self.focus = RigolAdminGUI.Focus.UNKNOWN

        frm_amplitude.bind("<FocusIn>", _handle_frm_amplitude_focus_in)

        frm_amplitude.bind("<FocusOut>", _handle_frm_amplitude_focus_out)

    def _ui_build_frequency(self, frm_app: tk.Frame):
        frm_frequency = tk.Frame(
            master=frm_app,
            background="blue",
            height=200,
            borderwidth=5,
        )
        lbl_frequency = ttk.Label(
            master=frm_frequency,
            text="Frequency:",
        )
        ent_frequency = ttk.Entry(
            master=frm_frequency,
            name="frequency",
            width=50,
            # textvariable=self.frequency_string_var,
            validatecommand=self.update_frequency,
        )
        ent_frequency["text"] = f"{self.data.frequency}"

        self.ent_frequency = ent_frequency

        frm_frequency.pack(
            side=tk.TOP,
            fill=tk.X,
            expand=True,
        )
        lbl_frequency.grid(row=0, column=0, sticky="e", ipadx=10)
        ent_frequency.grid(row=0, column=1)

        def _handle_frm_frequency_focus_in(event):
            console.log(f"[FOCUS IN]: frm_frequency")
            self.focus = RigolAdminGUI.Focus.FREQUENCY

        def _handle_frm_frequency_focus_out(event):
            console.log(f"[FOCUS OUT]: frm_frequency")
            self.focus = RigolAdminGUI.Focus.UNKNOWN

        frm_frequency.bind("<FocusIn>", _handle_frm_frequency_focus_in)

        frm_frequency.bind("<FocusOut>", _handle_frm_frequency_focus_out)

    def _ui_build_read_voltage(self, frm_app: tk.Frame):
        frm_read_voltage = tk.Frame(
            master=frm_app,
            background="green",
            height=200,
            borderwidth=5,
        )
        lbl_read_voltage_title = ttk.Label(master=frm_read_voltage, text="Voltage Read")
        frm_read_voltage.pack(
            side=tk.TOP,
            fill=tk.X,
            expand=True,
        )
        frm_read_voltage.rowconfigure([0, 1, 2, 3, 4], minsize=50)
        frm_read_voltage.columnconfigure([0, 1, 2, 3, 4], minsize=50)
        lbl_read_voltage_title.grid(row=0, column=0, columnspan=3, pady=30)

        for idx, channel in enumerate(self.channels, start=1):
            lbl_channel = ttk.Label(master=frm_read_voltage, text=channel)
            lbl_Vrms = ttk.Label(master=frm_read_voltage)
            lbl_Vpp = ttk.Label(master=frm_read_voltage)
            lbl_VdBu = ttk.Label(master=frm_read_voltage)

            self.data.lbls.append(
                (LockValue(lbl_Vrms), LockValue(lbl_Vpp), LockValue(lbl_VdBu))
            )

            lbl_channel.grid(row=idx, column=0, ipadx=20, sticky="ew")
            lbl_Vrms.grid(row=idx, column=1, ipadx=20, sticky="ew")
            lbl_VdBu.grid(row=idx, column=2, ipadx=20, sticky="ew")
            lbl_Vpp.grid(row=idx, column=3, ipadx=20, sticky="ew")

        lbl_gain = ttk.Label(master=frm_read_voltage, text="Gain (dB)")
        lbl_gain_value = ttk.Label(master=frm_read_voltage)

        self.data.gain = LockValue(lbl_gain_value)

        lbl_gain.grid(row=3, column=0, ipadx=20, sticky="ew")
        lbl_gain_value.grid(row=3, column=1, ipadx=20, sticky="ew")

        lbl_phase = ttk.Label(master=frm_read_voltage, text="Phase (deg)")
        lbl_phase_value = ttk.Label(master=frm_read_voltage)

        self.data.phase = LockValue(lbl_phase_value)

        lbl_phase.grid(row=4, column=0, ipadx=20, sticky="ew")
        lbl_phase_value.grid(row=4, column=1, ipadx=20, sticky="ew")

    def _ui_build_on_off(self, frm_app: tk.Frame):
        # ON - OFF
        frm_on_off = tk.Frame(
            master=frm_app,
            background="#abcdef",
            height=200,
            borderwidth=5,
        )
        btn_on = ttk.Button(master=frm_on_off, text="ON", command=self.device_turn_on)
        btn_off = ttk.Button(
            master=frm_on_off, text="OFF", command=self.device_turn_off
        )

        frm_on_off.pack(
            side=tk.TOP,
            fill=tk.X,
            expand=True,
        )
        btn_on.grid(row=0, column=0)
        btn_off.grid(row=0, column=1)

    def __init__(self) -> None:
        self.amplitude = 1
        self.n_sample = 100
        self.fs_multiplier = 50
        self.amplitude_mode = VoltageMode.Vpp

        self.rms_value_safe = LockValue[float](0.0)
        self.b_on = False

        self.focus = RigolAdminGUI.Focus.UNKNOWN
        self.amplitude_mode = VoltageMode.Vpp

        self.windows = tk.Tk()
        self.windows.wm_title("Rigol Admin Panel")
        self.windows.geometry("600x400")
        # self.windows.columnconfigure(0, minsize=250)
        # self.windows.rowconfigure(0, minsize=200)

        self.amplitude_mode_curr_string_var = StringVar(value=self.amplitude_mode.name)
        # amplitude_mode_curr_string_var.trace_add("write", self.on_amplitude_mode_change)

        self.amplitude_var = DoubleVar(value=self.amplitude)
        self.amplitude_var.trace_add("write", self.on_amplitude_change)

        self.amplitude_multiplier_var = DoubleVar(value=1)

        self.on_off_state = BooleanVar(value=False)
        self.on_off_state.trace_add("write", callback=self._handle_on_off)

        self.data = RmsDataParameters(
            frequency=LockValue(1000),
            Fs_multiplier=LockValue(50),
        )
        self._init_instruments()
        self.data.device = LockValue(self.device)

        self._ui_build()

        self.windows.bind("<Key>", self._handle_keypress)

        self.thread = Thread(target=update_rms_value, args=(self.data,))
        self.thread.start()

    def start_loop(self):
        self.windows.mainloop()

    # Create an event handler
    def _handle_keypress(self, event):
        """Print the character associated to the key pressed"""
        console.log(event)

        if event.char == "\x11":
            self.device_turn_off()
            self.generator.close()
            self.windows.destroy()

        if event.char == "\x06":  # CTRL + f
            self.ent_frequency.focus_set()
        if event.char == "\x01":  # CTRL + a
            self.ent_amplitude.focus_set()

        if event.keycode == 65 and event.state == 20:
            console.log("[KEY PRESSED]: SPACEBAR")
            self.on_off_state.set(not self.on_off_state.get())

        from tkinter import EventType

        if self.focus == RigolAdminGUI.Focus.AMPLITUDE:
            if event.keycode == 111 and event.state == 20:
                self.amplitude_var.set(
                    round(
                        self.amplitude_var.get() + self.amplitude_multiplier_var.get(),
                        3,
                    )
                )
            if event.keycode == 116 and event.state == 20:
                self.amplitude_var.set(
                    round(
                        self.amplitude_var.get() - self.amplitude_multiplier_var.get(),
                        3,
                    )
                )
            if event.keycode == 112 and event.state == 20:
                curr_multiplier = self.amplitude_multiplier_var.get()
                next_multiplier = curr_multiplier * 10
                if curr_multiplier == 1.0:
                    next_multiplier = 0.001

                self.amplitude_multiplier_var.set(next_multiplier)

            if event.keycode == 117 and event.state == 20:
                curr_multiplier = self.amplitude_multiplier_var.get()
                next_multiplier = curr_multiplier / 10
                if curr_multiplier == 0.001:
                    next_multiplier = 1.0

                self.amplitude_multiplier_var.set(next_multiplier)

    def _handle_amplitude_mode_Vpp(self):
        new_voltage_mode = VoltageMode.Vpp
        new_amplitude = voltage_converter(
            self.amplitude_var.get(),
            frm=self.amplitude_mode,
            to=new_voltage_mode,
        )

        console.log(
            f"[AMPLITUDE_MODE]: {self.amplitude_mode.name} -> {new_voltage_mode.name}"
        )
        console.log(
            f"[AMPLITUDE_STRING]: {self.amplitude_var.get()} -> {new_amplitude}"
        )

        self.amplitude_mode_curr_string_var.set(new_voltage_mode.name)
        self.amplitude_var.set(round(new_amplitude, 3))

    def _handle_amplitude_mode_Vrms(self):
        new_voltage_mode = VoltageMode.Vrms
        new_amplitude = voltage_converter(
            self.amplitude_var.get(),
            frm=self.amplitude_mode,
            to=new_voltage_mode,
        )

        console.log(
            f"[AMPLITUDE_MODE]: {self.amplitude_mode.name} -> {new_voltage_mode.name}"
        )
        console.log(
            f"[AMPLITUDE_STRING]: {self.amplitude_var.get()} -> {new_amplitude}"
        )

        self.amplitude_mode_curr_string_var.set(new_voltage_mode.name)
        self.amplitude_var.set(round(new_amplitude, 3))

    def _handle_amplitude_mode_VdBu(self):
        new_voltage_mode = VoltageMode.VdBu
        new_amplitude = voltage_converter(
            self.amplitude_var.get(),
            frm=self.amplitude_mode,
            to=new_voltage_mode,
        )

        console.log(
            f"[AMPLITUDE_MODE]: {self.amplitude_mode.name} -> {new_voltage_mode.name}"
        )
        console.log(
            f"[AMPLITUDE_STRING]: {self.amplitude_var.get()} -> {new_amplitude}"
        )

        self.amplitude_mode_curr_string_var.set(new_voltage_mode.name)
        self.amplitude_var.set(round(new_amplitude, 3))

    def _handle_on_off(self, *args):
        if self.on_off_state.get():
            self.device_turn_on()
        else:
            self.device_turn_off()

    # def _handle_rms_Vrms(self, *args):
    #     with self.data.rms_Vrms_var_safe.lock:
    #         self.lbl_Vrms.config(
    #             text="{:.5f} Vrms".format(self.data.rms_Vrms_var_safe.value.get())
    #         )

    # def _handle_rms_Vpp(self, *args):
    #     with self.data.rms_Vpp_var_safe.lock:
    #         self.lbl_Vpp.config(
    #             text="{:.5f} Vpp".format(self.data.rms_Vpp_var_safe.value.get())
    #         )

    # def _handle_rms_VdBu(self, *args):
    #     with self.data.rms_VdBu_var_safe.lock:
    #         self.lbl_VdBu.config(
    #             text="{:.5f} VdBu".format(self.data.rms_VdBu_var_safe.value.get())
    #         )

    def _init_instruments(self):
        # Asks for the 2 instruments
        list_devices: List[Instrument] = UsbTmc.search_devices()

        generator: UsbTmc = UsbTmc(list_devices[0])

        self.generator = generator

        self.generator.open()

        # Sets the Configuration for the Voltmeter
        generator_configs: list = [
            SCPI.clear(),
            SCPI.set_output(1, Switch.OFF),
            SCPI.set_function_voltage_ac(),
            SCPI.set_voltage_ac_bandwidth(Bandwidth.MIN),
            SCPI.set_source_voltage_amplitude(1, round(self.amplitude, 5)),
            SCPI.set_source_frequency(1, round(self.data.frequency.value, 5)),
        ]
        SCPI.exec_commands(self.generator, generator_configs)

        self.device = ni9223(self.n_sample)

        self.device.create_task("Rigol Admin")

        self.device.add_ai_channel(self.channels)

    def update_frequency(self):
        with self.data.frequency.lock:
            # Sets the Configuration for the Voltmeter
            generator_configs: list = [
                SCPI.set_source_frequency(1, round(self.data.frequency.value, 5)),
            ]

            SCPI.exec_commands(self.generator, generator_configs)

    def update_amplitude(self):
        # Sets the Configuration for the Voltmeter
        generator_configs: list = [
            SCPI.set_source_voltage_amplitude(1, round(self.amplitude, 5)),
        ]

        SCPI.exec_commands(self.generator, generator_configs)

    def device_turn_on(self):
        generator_configs: list = [
            SCPI.set_output(1, Switch.ON),
        ]
        SCPI.exec_commands(self.generator, generator_configs)
        console.log("[DEVICE]: TURN ON")

    def device_turn_off(self):
        generator_configs: list = [
            SCPI.set_output(1, Switch.OFF),
        ]
        SCPI.exec_commands(self.generator, generator_configs)
        console.log("[DEVICE]: TURN OFF")

    def on_frequency_change(self, *args):
        with self.data.frequency.lock:
            new_frequency: float
            try:
                new_frequency = float(self.data.frequency.value)
                if new_frequency == 0:
                    new_frequency = self.data.frequency.value

            except Exception:
                new_frequency = self.data.frequency.value

            console.log(
                f"[FREQUENCY]: '{self.data.frequency.value} Hz' -> '{new_frequency}' Hz"
            )

            self.data.frequency.value = new_frequency
            self.update_frequency()

    def on_amplitude_change(self, *args):
        curr_amplitude = self.amplitude
        curr_mode = self.amplitude_mode
        next_mode = VoltageMode[self.amplitude_mode_curr_string_var.get()]

        next_amplitude: float
        try:
            next_amplitude = self.amplitude_var.get()
        except Exception:
            next_amplitude = 0

        console.log(
            f"[AMPLITUDE]: '{curr_amplitude}' {curr_mode.name} -> '{next_amplitude}' {next_mode.name}"
        )

        self.amplitude_mode = next_mode
        self.amplitude = voltage_converter(
            next_amplitude,
            frm=self.amplitude_mode,
            to=VoltageMode.Vpp,
        )

        console.log(f"[RIGOL AMPLITUDE]: {self.amplitude} Vpp")
        self.update_amplitude()


class UpdateRms(Thread):
    device: ni9223
    data: RmsDataParameters

    def __init__(self, device: ni9223, data: RmsDataParameters) -> None:
        Thread.__init__(self)
        self.device = device
        self.data = data


def update_rms_value(data: RmsDataParameters):
    while True:
        Fs: Optional[float] = None
        with data.frequency.lock, data.Fs_multiplier.lock:
            Fs = trim_value(
                data.frequency.value * data.Fs_multiplier.value, max_value=1000000
            )
        if Fs is not None:
            with data.device.lock:
                data.device.value.set_sampling_clock_timing(Fs)
        voltages = []
        with data.device.lock:
            data.device.value.task_start()
            voltages = data.device.value.read_multi_voltages()
            data.device.value.task_stop()

        voltages_sampling_n: List[VoltageSampling] = []

        for voltage_sampling in voltages:
            voltages_sampling_n.append(
                VoltageSampling.from_list(voltage_sampling, data.frequency, Fs)
            )

        from audio.math.rms import RMSResult

        rms_result_n: List[RMSResult] = []

        for volts in voltages_sampling_n:
            rms_result_n.append(RMS.rms_v2(volts, interpolation_rate=20))

        voltage_rms_values: List[Tuple[float, float, float]] = []

        for result in rms_result_n:
            Vrms = result.rms
            Vpp = Vrms_to_Vpp(Vrms)
            VdBu = Vrms_to_VdBu(Vrms)
            voltage_rms_values.append((Vrms, Vpp, VdBu))

        for lbls, values in zip(data.lbls, voltage_rms_values):

            lblVrms, lblVpp, lblVdBu = lbls
            Vrms, Vpp, VdBu = values

            with lblVrms.lock:
                lblVrms.value["text"] = f"{Vrms:.05f} Vrms"
            with lblVpp.lock:
                lblVpp.value["text"] = f"{Vpp:.05f} Vpp"
            with lblVdBu.lock:
                lblVdBu.value["text"] = f"{VdBu:.05f} VdBu"

        import time
        from audio.math.voltage import calculate_gain_dB

        gain_dB = calculate_gain_dB(voltage_rms_values[1][1], voltage_rms_values[0][1])
        with data.gain.lock:

            data.gain.value["text"] = f"{gain_dB:.05f}"

        # if abs(gain_dB) > 1:
        #     time.sleep(5)

        from audio.math.phase import phase_offset_v2

        v_0 = rms_result_n[0].voltages
        v_1 = rms_result_n[1].voltages

        with data.frequency.lock:
            freq = data.frequency.value
            volts_0 = VoltageSampling.from_list(v_0, freq, Fs * 20)
            volts_1 = VoltageSampling.from_list(v_1, freq, Fs * 20)

        phase_offset = phase_offset_v2(volts_0, volts_1)

        if phase_offset is not None:

            with data.phase.lock:
                data.phase.value["text"] = f"{phase_offset:.05f}"
