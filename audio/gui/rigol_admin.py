from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from enum import Enum, auto
from threading import Lock, Thread
from tkinter import BooleanVar, DoubleVar, Event, EventType, Frame, Misc, StringVar, ttk
from typing import TYPE_CHECKING, Generic, NoReturn, Self, TypeVar

import click

from audio.exception.device import DeviceNotFoundError
from audio.math.voltage import calculate_gain_db

if TYPE_CHECKING:
    import usb

from audio.console import console
from audio.device.cdaq import Ni9223
from audio.math.interpolation import InterpolationKind
from audio.math.phase import phase_offset_v4
from audio.math.rms import RMS, RMS_MODE
from audio.math.voltage import VoltageMode, Vrms_to_VdBu, Vrms_to_Vpp, voltage_converter
from audio.model.sampling import VoltageSamplingV2
from audio.usb.usbtmc import ResourceManager, UsbTmc
from audio.utility import trim_value
from audio.utility.scpi import SCPI, Bandwidth, Switch

KEY_CTRL = 20
KEY_SPACEBAR = 65
KEY_PAGE_UP_PRIOR = 112
KEY_PAGE_DOWN_NEXT = 117
KEY_ARROW_UP = 111
KEY_ARROW_DOWN = 116

rms_data_lock: Lock = Lock()


T = TypeVar("T")


class LockValue(Generic[T]):
    lock: Lock
    value: T

    def __init__(self: Self, value: T) -> None:
        self.lock = Lock()
        self.value = value


@click.command()
def rigol_admin() -> None:
    console.log("HELLO GUI")
    rigol_admin_gui: RigolAdminGUI = RigolAdminGUI()
    rigol_admin_gui.start_loop()


@dataclass
class RmsDataParameters:
    frequency: LockValue[float]
    Fs_multiplier: LockValue[float]
    device: LockValue[Ni9223] | None = None
    gain: LockValue[ttk.Label] | None = None
    phase: LockValue[ttk.Label] | None = None

    lbls: list[
        tuple[LockValue[ttk.Label], LockValue[ttk.Label], LockValue[ttk.Label]]
    ] = field(default_factory=list)


class RigolAdminGUI:
    windows: tk.Tk
    generator: UsbTmc
    device: Ni9223
    b_on: bool
    amplitude_steps: list[float] = [1.0, 0.1, 0.01, 0.001]
    amplitude_steps_index: int = 0

    channels: list[str] = [
        "cDAQ9189-1CDBE0AMod5/ai1",
        "cDAQ9189-1CDBE0AMod5/ai3",
    ]

    amplitude_mode: VoltageMode
    amplitude: float
    n_sample: int
    fs_multiplier: int

    data: RmsDataParameters

    lbl_voltage_rms: ttk.Label
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

    def _ui_build(self: Self) -> None:
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
        self._ui_build_read_voltage(frm_app=frm_app)
        self._ui_build_on_off(frm_app=frm_app)

    def _ui_build_amplitude_modes(self: Self, frm_app: tk.Frame) -> None:
        frm_amplitude_modes = tk.Frame(
            master=frm_app,
            borderwidth=5,
            background="red",
        )
        lbl_amplitude_modes = ttk.Label(
            master=frm_amplitude_modes,
            text="Amplitude Modes:",
        )

        btn_amplitude_modes_voltage_peak_to_peak = ttk.Button(
            master=frm_amplitude_modes,
            text=VoltageMode.Vpp.name,
            command=self._handle_amplitude_mode_voltage_peak_to_peak,
        )
        btn_amplitude_modes_voltage_rms = ttk.Button(
            master=frm_amplitude_modes,
            text=VoltageMode.Vrms.name,
            command=self._handle_amplitude_mode_voltage_rms,
        )
        btn_amplitude_modes_voltage_dbu = ttk.Button(
            master=frm_amplitude_modes,
            text=VoltageMode.VdBu.name,
            command=self._handle_amplitude_mode_voltage_dbu,
        )

        frm_amplitude_modes.pack(
            side=tk.TOP,
            fill=tk.X,
            expand=True,
        )
        lbl_amplitude_modes.grid(row=0, column=0, sticky="e", ipadx=10)
        btn_amplitude_modes_voltage_peak_to_peak.grid(row=0, column=1, ipadx=5)
        btn_amplitude_modes_voltage_rms.grid(row=0, column=2, ipadx=5)
        btn_amplitude_modes_voltage_dbu.grid(row=0, column=3, ipadx=5)

    def _ui_build_amplitude(self: Self, frm_app: tk.Frame) -> None:
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
            master=frm_amplitude,
            width=15,
            textvariable=self.amplitude_var,
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

        for idx, step in enumerate(self.amplitude_steps, start=3):
            ttk.Radiobutton(
                master=frm_amplitude,
                text=str(step),
                variable=self.amplitude_multiplier_var,
                value=step,
            ).grid(row=0, column=idx, sticky="e")

        self.amplitude_multiplier_var.set(
            self.amplitude_steps[self.amplitude_steps_index],
        )

        def _handle_frm_amplitude_focus_in(
            _event: Event[Frame],
        ) -> None:
            console.log("[FOCUS IN]: frm_amplitude")
            self.focus = RigolAdminGUI.Focus.AMPLITUDE

        def _handle_frm_amplitude_focus_out(
            _event: Event[Frame],
        ) -> None:
            console.log("[FOCUS OUT]: frm_amplitude")
            self.focus = RigolAdminGUI.Focus.UNKNOWN

        frm_amplitude.bind("<FocusIn>", _handle_frm_amplitude_focus_in)

        frm_amplitude.bind("<FocusOut>", _handle_frm_amplitude_focus_out)

    def _ui_build_frequency(self: Self, frm_app: tk.Frame) -> None:
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

        def _handle_frm_frequency_focus_in(
            _event: Event[Frame],
        ) -> None:
            console.log("[FOCUS IN]: frm_frequency")
            self.focus = RigolAdminGUI.Focus.FREQUENCY

        def _handle_frm_frequency_focus_out(
            _event: Event[Frame],
        ) -> None:
            console.log("[FOCUS OUT]: frm_frequency")
            self.focus = RigolAdminGUI.Focus.UNKNOWN

        frm_frequency.bind("<FocusIn>", _handle_frm_frequency_focus_in)

        frm_frequency.bind("<FocusOut>", _handle_frm_frequency_focus_out)

    def _ui_build_read_voltage(self: Self, frm_app: tk.Frame) -> None:
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
            lbl_voltage_rms = ttk.Label(master=frm_read_voltage)
            lbl_voltage_peak_to_peak = ttk.Label(master=frm_read_voltage)
            lbl_voltage_dbu = ttk.Label(master=frm_read_voltage)

            _type = type[self.data.lbls]

            self.data.lbls.append(
                (
                    LockValue(lbl_voltage_rms),
                    LockValue(lbl_voltage_peak_to_peak),
                    LockValue(lbl_voltage_dbu),
                ),
            )

            lbl_channel.grid(row=idx, column=0, ipadx=20, sticky="ew")
            lbl_voltage_rms.grid(row=idx, column=1, ipadx=20, sticky="ew")
            lbl_voltage_dbu.grid(row=idx, column=2, ipadx=20, sticky="ew")
            lbl_voltage_peak_to_peak.grid(row=idx, column=3, ipadx=20, sticky="ew")

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

    def _ui_build_on_off(self: Self, frm_app: tk.Frame) -> None:
        # ON - OFF
        frm_on_off = tk.Frame(
            master=frm_app,
            background="#abcdef",
            height=200,
            borderwidth=5,
        )
        btn_on = ttk.Button(master=frm_on_off, text="ON", command=self.device_turn_on)
        btn_off = ttk.Button(
            master=frm_on_off,
            text="OFF",
            command=self.device_turn_off,
        )

        frm_on_off.pack(
            side=tk.TOP,
            fill=tk.X,
            expand=True,
        )
        btn_on.grid(row=0, column=0)
        btn_off.grid(row=0, column=1)

    def __init__(self: Self) -> None:
        self.amplitude = 0
        self.n_sample = 500
        self.fs_multiplier = 50
        self.amplitude_mode = VoltageMode.VdBu

        self.rms_value_safe = LockValue[float](0.0)
        self.b_on = False

        self.focus = RigolAdminGUI.Focus.UNKNOWN

        self.windows = tk.Tk()
        self.windows.wm_title("Rigol Admin Panel")
        self.windows.geometry("600x400")
        self.amplitude_mode_curr_string_var = StringVar(value=self.amplitude_mode.name)

        self.amplitude_var = DoubleVar(value=self.amplitude)
        self.amplitude_var.trace_add("write", self.on_amplitude_change)
        self.amplitude_var.set(-5.95)

        self.amplitude_multiplier_var = DoubleVar(value=1)

        self.on_off_state = BooleanVar(value=False)
        self.on_off_state.trace_add("write", callback=self._handle_on_off)

        self.data = RmsDataParameters(
            frequency=LockValue(200000),
            Fs_multiplier=LockValue(50),
        )
        self._init_instruments()
        self.data.device = LockValue(self.device)

        self._ui_build()

        self.windows.bind(sequence="<Key>", func=self._handle_keypress)

        self.thread = Thread(target=update_rms_value, args=(self.data,))
        self.thread.start()

    def start_loop(self: Self) -> None:
        self.windows.mainloop()

    # Create an event handler
    def _handle_keypress(
        self: Self,
        event: Event[Misc],
    ) -> None:
        """Print the character associated to the key pressed"""
        console.log("[EVENT]:", event)

        if event.char == "\x11":
            self.device_turn_off()
            self.generator.close()
            self.windows.destroy()

        if event.keycode == KEY_SPACEBAR and event.state == KEY_CTRL:
            console.log("[KEY PRESSED]: SPACEBAR")
            self.on_off_state.set(not self.on_off_state.get())

        if (
            self.focus == RigolAdminGUI.Focus.AMPLITUDE
            and event.type == EventType.KeyPress
        ):
            if event.keycode == KEY_ARROW_UP and event.state == KEY_CTRL:
                self.amplitude_var.set(
                    round(
                        self.amplitude_var.get() + self.amplitude_multiplier_var.get(),
                        3,
                    ),
                )
            if event.keycode == KEY_ARROW_DOWN and event.state == KEY_CTRL:
                self.amplitude_var.set(
                    round(
                        self.amplitude_var.get() - self.amplitude_multiplier_var.get(),
                        3,
                    ),
                )

            if event.keycode == KEY_PAGE_UP_PRIOR and event.state == KEY_CTRL:
                self.amplitude_steps_index = max(0, self.amplitude_steps_index - 1)
                self.amplitude_multiplier_var.set(
                    self.amplitude_steps[self.amplitude_steps_index],
                )
                console.log(
                    "[Amplitude Step]: ",
                    self.amplitude_steps[self.amplitude_steps_index],
                )

            if event.keycode == KEY_PAGE_DOWN_NEXT and event.state == KEY_CTRL:
                self.amplitude_steps_index = min(
                    len(self.amplitude_steps) - 1,
                    self.amplitude_steps_index + 1,
                )
                self.amplitude_multiplier_var.set(
                    self.amplitude_steps[self.amplitude_steps_index],
                )
                console.log(
                    "[Amplitude Step]: ",
                    self.amplitude_steps[self.amplitude_steps_index],
                )

    def _handle_amplitude_mode_voltage_peak_to_peak(self: Self) -> None:
        new_voltage_mode = VoltageMode.Vpp
        new_amplitude = voltage_converter(
            self.amplitude_var.get(),
            frm=self.amplitude_mode,
            to=new_voltage_mode,
        )

        console.log(
            f"[AMPLITUDE_MODE]: {self.amplitude_mode.name} -> {new_voltage_mode.name}",
        )
        console.log(
            f"[AMPLITUDE_STRING]: {self.amplitude_var.get()} -> {new_amplitude}",
        )

        self.amplitude_mode_curr_string_var.set(new_voltage_mode.name)
        self.amplitude_var.set(round(new_amplitude, 3))

    def _handle_amplitude_mode_voltage_rms(self: Self) -> None:
        new_voltage_mode = VoltageMode.Vrms
        new_amplitude = voltage_converter(
            self.amplitude_var.get(),
            frm=self.amplitude_mode,
            to=new_voltage_mode,
        )

        console.log(
            f"[AMPLITUDE_MODE]: {self.amplitude_mode.name} -> {new_voltage_mode.name}",
        )
        console.log(
            f"[AMPLITUDE_STRING]: {self.amplitude_var.get()} -> {new_amplitude}",
        )

        self.amplitude_mode_curr_string_var.set(new_voltage_mode.name)
        self.amplitude_var.set(round(new_amplitude, 3))

    def _handle_amplitude_mode_voltage_dbu(self: Self) -> None:
        new_voltage_mode = VoltageMode.VdBu
        new_amplitude = voltage_converter(
            self.amplitude_var.get(),
            frm=self.amplitude_mode,
            to=new_voltage_mode,
        )

        console.log(
            f"[AMPLITUDE_MODE]: {self.amplitude_mode.name} -> {new_voltage_mode.name}",
        )
        console.log(
            f"[AMPLITUDE_STRING]: {self.amplitude_var.get()} -> {new_amplitude}",
        )

        self.amplitude_mode_curr_string_var.set(new_voltage_mode.name)
        self.amplitude_var.set(round(new_amplitude, 3))

    def _handle_on_off(self: Self, *args: tuple[str, str, str]) -> None:
        *_, mode = args
        if mode == "write":
            if self.on_off_state.get():
                self.device_turn_on()
            else:
                self.device_turn_off()

    def _init_instruments(self: Self) -> None:
        # Asks for the 2 instruments
        rm: ResourceManager = ResourceManager()
        list_devices: list[usb.core.Device] = rm.search_resources()

        if len(list_devices) < 1:
            raise DeviceNotFoundError

        self.generator = rm.open_resource(list_devices[0])

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

        self.device = Ni9223(self.n_sample)

        self.device.create_task("Rigol Admin")

        self.device.add_ai_channel(self.channels)

    def update_frequency(self: Self) -> None:
        with self.data.frequency.lock:
            # Sets the Configuration for the Voltmeter
            generator_configs: list = [
                SCPI.set_source_frequency(1, round(self.data.frequency.value, 5)),
            ]

            SCPI.exec_commands(self.generator, generator_configs)

    def update_amplitude(self: Self) -> None:
        # Sets the Configuration for the Voltmeter
        generator_configs: list = [
            SCPI.set_source_voltage_amplitude(1, round(self.amplitude, 5)),
        ]

        SCPI.exec_commands(self.generator, generator_configs)

    def device_turn_on(self: Self) -> None:
        generator_configs: list = [
            SCPI.set_output(1, Switch.ON),
        ]
        SCPI.exec_commands(self.generator, generator_configs)
        console.log("[DEVICE]: TURN ON")

    def device_turn_off(self: Self) -> None:
        generator_configs: list = [
            SCPI.set_output(1, Switch.OFF),
        ]
        SCPI.exec_commands(self.generator, generator_configs)
        console.log("[DEVICE]: TURN OFF")

    def on_amplitude_change(self: Self, *args: tuple[str, str, str]) -> None:
        *_, mode = args
        if mode != "write":
            return
        curr_amplitude: float = self.amplitude
        curr_mode: VoltageMode = self.amplitude_mode
        next_mode: VoltageMode = VoltageMode[self.amplitude_mode_curr_string_var.get()]

        next_amplitude: float
        try:
            next_amplitude = self.amplitude_var.get()
        except Exception:  # noqa: BLE001
            next_amplitude = 0

        console.log(
            f"[AMPLITUDE]: '{curr_amplitude}' {curr_mode.name} -> '{next_amplitude}' {next_mode.name}",
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
    device: Ni9223
    data: RmsDataParameters

    def __init__(self: Self, device: Ni9223, data: RmsDataParameters) -> None:
        Thread.__init__(self)
        self.device = device
        self.data = data


def update_rms_value(  # noqa: C901, PLR0912, PLR0915
    data: RmsDataParameters,
) -> NoReturn:
    while True:
        sampling_frequency: float | None = None
        with data.frequency.lock, data.Fs_multiplier.lock:
            sampling_frequency = trim_value(
                value=data.frequency.value * data.Fs_multiplier.value,
                max_value=1000000,
            )
        if sampling_frequency is not None:
            with data.device.lock:
                data.device.value.set_sampling_clock_timing(sampling_frequency)
        voltages = []
        with data.device.lock:
            data.device.value.task_start()
            voltages = data.device.value.read_multi_voltages()
            data.device.value.task_stop()

        voltages_sampling_n: list[VoltageSamplingV2] = []

        with data.frequency.lock:
            frequency = data.frequency.value
        for voltage_sampling in voltages:
            voltages_sampling_n.append(
                VoltageSamplingV2.from_list(
                    voltage_sampling,
                    frequency,
                    sampling_frequency,
                ).augment_interpolation(
                    interpolation_rate=50,
                    interpolation_mode=InterpolationKind.CUBIC,
                ),
            )

        rms_result_n: list[float | None] = []

        for volts in voltages_sampling_n:
            rms_result_n.append(
                RMS.rms_v3(
                    voltages_sampling=volts,
                    trim=True,
                    rms_mode=RMS_MODE.FFT,
                ),
            )

        voltage_rms_values: list[tuple[float, float, float]] = []

        for result in rms_result_n:
            if result is None:
                voltage_rms_values.append((0, 0, 0))
            else:
                voltage_rms = result
                voltage_peak_to_peak = Vrms_to_Vpp(voltage_rms)
                voltage_dbu = Vrms_to_VdBu(voltage_rms)
                voltage_rms_values.append(
                    (voltage_rms, voltage_peak_to_peak, voltage_dbu),
                )

        for lbls, values in zip(data.lbls, voltage_rms_values, strict=True):
            lbl_voltage_rms, lbl_voltage_peak_to_peak, lbl_voltage_dbu = lbls
            voltage_rms, voltage_peak_to_peak, voltage_dbu = values

            with lbl_voltage_rms.lock:
                lbl_voltage_rms.value["text"] = f"{voltage_rms:.05f} Vrms"
            with lbl_voltage_peak_to_peak.lock:
                lbl_voltage_peak_to_peak.value[
                    "text"
                ] = f"{voltage_peak_to_peak:.05f} Vpp"
            with lbl_voltage_dbu.lock:
                lbl_voltage_dbu.value["text"] = f"{voltage_dbu:.05f} VdBu"

        gain_db = calculate_gain_db(
            Vin=voltage_rms_values[0][0],
            Vout=voltage_rms_values[1][0],
        )
        with data.gain.lock:
            data.gain.value["text"] = f"{gain_db:.05f}"

        if voltages_sampling_n[0] is None or voltages_sampling_n[1] is None:
            with data.phase.lock:
                data.phase.value["text"] = "NONE"
        else:
            volts_0 = voltages_sampling_n[0]
            volts_1 = voltages_sampling_n[1]

            try:
                phase_offset = phase_offset_v4(volts_0, volts_1)

            except Exception as e:  # noqa: BLE001
                console.log(f"{e}")
                phase_offset = None

            if phase_offset is not None:
                with data.phase.lock:
                    data.phase.value["text"] = f"{phase_offset:.05f}"
            else:
                with data.phase.lock:
                    data.phase.value["text"] = "NONE"
