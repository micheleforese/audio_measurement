#!/usr/bin/env python3

from distutils.log import debug
from cDAQ.timer import Timer
from platform import system
from rich.console import Console
from rich import pretty
from rich.panel import Panel
from nidaqmx import *
import nidaqmx.system
import numpy
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

curva("config/curva.json", debug=True)
