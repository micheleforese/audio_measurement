from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk
from enum import Enum, auto
from math import log10, sqrt
from time import sleep
from tkinter import BooleanVar, DoubleVar, IntVar, StringVar, Variable
from typing import List, Optional

import click
from rich.panel import Panel
from usbtmc import Instrument

from audio.console import console
from audio.math.rms import RMS
from audio.math.voltage import VoltageMode, Vrms_to_VdBu, Vrms_to_Vpp, voltage_converter
from audio.usb.usbtmc import UsbTmc
from audio.utility import trim_value
from audio.utility.scpi import SCPI, Bandwidth, Switch


@click.command()
def rigol_admin():
    console.log("HELLO GUI")
    rigol_admin_gui = RigolAdminGUI()


class RigolAdminGUI:

    windows: tk.Tk
    generator: UsbTmc
    b_on: bool

    amplitude_mode: VoltageMode
    amplitude: float
    frequency: float
    n_sample: int
    fs_multiplier: int
    rms_value: float

    lbl_Vrms: ttk.Label
    ent_frequency: ttk.Entry
    ent_amplitude: ttk.Entry

    amplitude_mode_curr_string_var: StringVar
    amplitude_var: DoubleVar
    amplitude_multiplier_var: DoubleVar
    amplitude_multiplier_list_radio_button: List[ttk.Radiobutton]
    frequency_string_var: StringVar

    on_off_state: BooleanVar

    class Focus(Enum):
        AMPLITUDE = auto()
        FREQUENCY = auto()
        UNKNOWN = auto()

    focus: Focus

    def __init__(self) -> None:
        self.amplitude = 1
        self.frequency = 1000
        self.n_sample = 100
        self.fs_multiplier = 50
        self.amplitude_mode = VoltageMode.Vpp

        self.rms_value = 0
        self.b_on = False

        self.focus = RigolAdminGUI.Focus.UNKNOWN

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
        self.amplitude_multiplier_list_radio_button = []

        self.frequency_string_var = StringVar(value=str(self.frequency))
        self.frequency_string_var.trace_add("write", self.on_frequency_change)

        self.on_off_state = BooleanVar(value=False)
        self.on_off_state.trace_add("write", callback=self._handle_on_off)

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

        self.amplitude_mode = VoltageMode.Vpp

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
            textvariable=self.frequency_string_var,
        )
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

        frm_read_voltage = tk.Frame(
            master=frm_app,
            background="green",
            height=200,
            borderwidth=5,
        )
        lbl_read_voltage_title = ttk.Label(master=frm_read_voltage, text="Voltage Read")
        lbl_Vrms = ttk.Label(master=frm_read_voltage)
        self.lbl_Vrms = lbl_Vrms
        lbl_VdBu = ttk.Label(master=frm_read_voltage)
        self.lbl_VdBu = lbl_VdBu
        lbl_Vpp = ttk.Label(master=frm_read_voltage)
        self.lbl_Vpp = lbl_Vpp

        frm_read_voltage.pack(
            side=tk.TOP,
            fill=tk.X,
            expand=True,
        )
        frm_read_voltage.rowconfigure([0, 1], minsize=50)
        frm_read_voltage.columnconfigure([0, 1, 2], minsize=50)
        lbl_read_voltage_title.grid(row=0, column=0, columnspan=3, ipady=30)
        lbl_Vrms.grid(row=1, column=0, ipadx=20, sticky="ew")
        lbl_VdBu.grid(row=1, column=1, ipadx=20, sticky="ew")
        lbl_Vpp.grid(row=1, column=2, ipadx=20, sticky="ew")

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

        self.windows.bind("<Key>", self._handle_keypress)

        self.init_instrument()

        self.update_rms_value()

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

    def init_instrument(self):
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
            SCPI.set_source_frequency(1, round(self.frequency, 5)),
            # SCPI.set_output_impedance(1, 50),
        ]
        SCPI.exec_commands(self.generator, generator_configs)

    def update_frequency(self):
        # Sets the Configuration for the Voltmeter
        generator_configs: list = [
            SCPI.set_source_frequency(1, round(self.frequency, 5)),
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

    def update_rms_value(self):

        Fs = trim_value(self.frequency * self.fs_multiplier, max_value=1000000)

        Vrms: Optional[float]

        _, Vrms = RMS.rms(
            frequency=self.frequency,
            Fs=Fs,
            ch_input="cDAQ9189-1CDBE0AMod5/ai0",
            max_voltage=10,
            min_voltage=-10,
            number_of_samples=self.n_sample,
            time_report=False,
            save_file=None,
            trim=True,
        )
        self.rms_value = float(Vrms)

        self.lbl_Vrms.config(text="{:.5f} Vrms".format(self.rms_value))

        Vpp = Vrms_to_Vpp(self.rms_value)
        self.lbl_Vpp.config(text="{:.5f} Vpp".format(Vpp))

        VdBu = Vrms_to_VdBu(self.rms_value)
        self.lbl_VdBu.config(text="{:.5f} VdBu".format(VdBu))

        self.lbl_Vrms.after(500, self.update_rms_value)

    def on_frequency_change(self, *args):
        new_frequency: float
        try:
            new_frequency = float(self.frequency_string_var.get())
            if new_frequency == 0:
                new_frequency = self.frequency

        except Exception:
            new_frequency = self.frequency

        console.log(f"[FREQUENCY]: '{self.frequency} Hz' -> '{new_frequency}' Hz")

        self.frequency = new_frequency
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
