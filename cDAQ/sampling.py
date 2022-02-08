

def test_sampling(file_path: str, min_Hz: np.int = 10, max_Hz: np.int = 100, points_for_decade: np.int = 10,
                  sample_number=1,
                  time_report: bool = False, debug: bool = False):

    table_config = Table(title="Configurations")
    table_config.add_column("Configuration", style="cyan", no_wrap=True)

    step: np.float = 1 / points_for_decade
    amplitude = 4.47
    frequency: np.float
    voltages_measurements: List[np.float]
    period: np.float = 0.0
    delay: np.float = 0.0
    aperture: np.float = 0.0
    interval: np.float = 0.0

    """Sets minimum for Delay, Aperture and Interval"""
    delay_min: np.float = 0.001
    aperture_min: np.float = 0.01
    interval_min: np.float = 0.01

    table_config.add_row("Step", f"{step}",
                         style="")
    table_config.add_row("Sample Number", f"{sample_number}",
                         style="")
    table_config.add_row("Amplitude", f"{amplitude}",
                         style="")

    start: datetime = 0
    stop: datetime = 0

    """Asks for the 2 instruments"""
    list_devices: List[Instrument] = get_device_list()
    print_devices_list(list_devices)
    index_generator: np.int = np.int(input("Which is the Generator? "))
    index_reader: np.int = np.int(input("Which is the Reader? "))

    table_config.add_row("Generator Index", f"{index_generator}",
                         style="")
    table_config.add_row("Reader Index", f"{index_reader}",
                         style="")

    """Generates the insttrument's interfaces"""
    gen: usbtmc.Instrument = list_devices[index_generator]
    read: usbtmc.Instrument = list_devices[index_reader]

    """Open the Instruments interfaces"""
    gen.open()
    read.open()

    """Sets the Configuration for the Voltmeter"""
    configs_gen: List[str] = [
        "*CLS",
        ":FUNCtion:VOLTage:AC",
        f":SOUR1:VOLTAGE:AMPLitude {amplitude}"
        ":OUTPut1 OFF",
        ":OUTPut1 ON",
    ]

    configs_read: List[str] = [
        "*CLS",
        "CONF:VOLT:AC",
        ":VOLT:AC:BAND +3.00000000E+00",
        ":TRIG:SOUR IMM",
        ":TRIG:DEL:AUTO OFF",
        ":FREQ:VOLT:RANG:AUTO ON",
        ":SAMP:SOUR TIM",
        f":SAMP:COUN {sample_number}",
    ]

    exec_commands(gen, configs_gen)
    exec_commands(read, configs_read)

    min_index: np.float = log10(min_Hz)
    max_index: np.float = log10(max_Hz)

    table_config.add_row("min Hz", f"{min_Hz}",
                         style="")
    table_config.add_row("max Hz", f"{max_Hz}",
                         style="")

    table_config.add_row("min index", f"{min_index}",
                         style="")
    table_config.add_row("max index", f"{max_index}",
                         style="")

    table_config.add_row("Generator Config SCPI", "\n".join(configs_gen),
                         style="")
    table_config.add_row("Reader Config SCPI", "\n".join(configs_read),
                         style="")

    step_max = points_for_decade * max_index
    step_min = points_for_decade * min_index
    step_total = step_max - step_min

    table_config.add_row("Step Max", f"{step_max}",
                         style="")
    table_config.add_row("Step Min", f"{step_min}",
                         style="")
    table_config.add_row("Step Total", f"{step_total}",
                         style="")

    console.print(table_config)

    """Open the file for the measurements"""
    f = open(file_path, "w")

    """Start time"""
    start = datetime.now()

    step_curr = 0
    while step_curr < step_total + 1:

        table_update = Table(
            Column(),
            Column(justify="right"),
            show_header=False
        )

        step_curr_Hz = min_index + step_curr * step
        # Frequency in Hz
        frequency = pow(10, step_curr_Hz)

        # Period in seconds
        period = 1 / frequency

        # Delay in seconds
        delay = period * 6
        delay = 1

        # Aperture in seconds
        aperture = period * 0.5

        # Interval in seconds
        # Interval is 10% more than aperture
        interval = period * 0.5

        if(delay < delay_min):
            delay = delay_min

        if(aperture < aperture_min):
            aperture = aperture_min

        if(interval < interval_min):
            interval = interval_min

        aperture *= 1.2
        interval *= 5

        delay = round(delay, 4)
        aperture = round(aperture, 4)
        interval = round(interval, 4)

        # Sets the Frequency
        gen.write(":SOURce1:FREQ {}".format(round(frequency, 5)))

        # Sets the aperture
        # read.write(f":VOLT:APER {aperture}")

        # Sets the delay between the trigger and the first measurement
        read.write("TRIG:DEL {}".format(delay))

        # Sets the interval of the measurements
        read.write(":SAMP:TIM {}".format(interval))

        # Init the measurements
        read.write("INIT")
        while(int(read.ask("*OPC?")) == 0):
            console.log("waiting")
            sleep(1)
        voltages_measurements = read.ask("FETCh?").split(",")

        """File Writing"""
        f.write("{},{}\n".format(frequency, ",".join(voltages_measurements)))

        """PRINTING"""
        if(debug):
            error = float(read.ask("*ESR?"))
            table_update.add_row("Step Curr", f"{step_curr}")
            table_update.add_row("Step Curr in log Hz", f"{step_curr_Hz}")
            table_update.add_row("Frequency", f"{frequency}")
            table_update.add_row("Period", f"{period}")
            table_update.add_row("Delay", f"{delay}")
            table_update.add_row("Aperture", f"{aperture}")
            table_update.add_row("Interval", f"{interval}")
            table_update.add_row("Voltages", "\n".join(voltages_measurements))
            if(error != 0):
                table_update.add_row("ERROR", f"{error}")

            console.print(table_update)

        step_curr += 1

    f.close()

    """Stop time"""
    stop = datetime.now()

    if(time_report):
        console.print(
            Panel(
                f"{(stop-start).total_seconds()} s",
                title="Execution Time"
            )
        )

    """Closes the Instruments interfaces"""
    gen.close()
    read.close()
