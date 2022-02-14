#!/usr/bin/env python3

from distutils.log import debug
from rich.panel import Panel
from nidaqmx import *
from cDAQ.timer import Timer
from cDAQ.utility import *
from cDAQ.test import *
from cDAQ.console import console
from cDAQ.curva import *


# 192.168.1.52 cDAQ


cdaq: cDAQ = cDAQ()

cdaq.print_driver_version()
cdaq.print_list_devices()


# test_thermocouple()
# test_ao_voltage()
# test_ai_voltage(ch_input=0)

# test_rigol_rms_ni_output(2, 40000, number_of_samples=100)

# curva("config/curva.json", debug=True)


def test_samp():
    number = 20

    csv_file = "data/filter/test_filter_{}.csv".format(number)
    png_file = "data/filter/test_filter_{}.png".format(number)

    test_sampling(csv_file, min_Hz=800, max_Hz=1800,
                  points_for_decade=100,
                  sample_number=20,
                  time_report=True, debug=True,
                  )

    plot_log_db(csv_file, png_file, number_voltages=20)

    diff_steps(csv_file)

    console.print("Finished")


# plot("config/config_template.json")


curva('test/basic.json', 'test/basic.csv', 'test/basic.png', debug=True)
