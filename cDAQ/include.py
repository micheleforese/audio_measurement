import enum
from os import read
from platform import system
from re import A
from time import clock
from typing import List
from nidaqmx._task_modules.channels.ai_channel import AIChannel
from nidaqmx._task_modules.channels.ao_channel import AOChannel
from nidaqmx.errors import DaqError, Error
from nidaqmx.task import Task
from nidaqmx.types import CtrFreq
from numpy.ma.core import shape
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.style import StyleType
from rich.tree import Tree
import nidaqmx
import nidaqmx.system
import nidaqmx.constants
import nidaqmx.stream_readers
import nidaqmx.stream_writers
import numpy as np
from cDAQ.utility import *
from usbTmc.UsbTmc import *
from usbTmc.utility import *
from pathlib import Path
from .utility import *
from scipy.fft import fft, fftfreq, rfft
from typing import List
from nidaqmx._task_modules.channels.ao_channel import AOChannel
from nidaqmx.system._collections.device_collection import DeviceCollection
from nidaqmx.system.system import System
from numpy.lib.function_base import average
from numpy.ma.core import sin, sqrt
from rich import table
from rich.console import Console
from rich import inspect, pretty
from rich.panel import Panel
from rich.table import Column, Table
import nidaqmx
import nidaqmx.system
from rich.tree import Tree
import numpy as np
import math
