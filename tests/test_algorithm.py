import numpy as np
import pytest

from cDAQ.alghorithm import LogaritmicScale
from cDAQ.console import console
from rich import inspect


def test_algorithm():

    log_scale: LogaritmicScale = LogaritmicScale(10, 1000, 10)
    console.print(inspect(log_scale))
    log_scale: LogaritmicScale = LogaritmicScale(20, 1000, 10)
    console.print(inspect(log_scale))
    log_scale: LogaritmicScale = LogaritmicScale(20, 1030, 10)
    console.print(inspect(log_scale))
    log_scale: LogaritmicScale = LogaritmicScale(
        np.math.pow(10, 1), np.math.pow(10, 3), 10
    )
    console.print(inspect(log_scale))
    log_scale: LogaritmicScale = LogaritmicScale(
        np.math.pow(10, 1), np.math.pow(10, 3.04), 20
    )
    console.print(inspect(log_scale))
