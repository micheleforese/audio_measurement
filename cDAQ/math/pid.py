from concurrent.futures import process
from typing import List, Optional

import numpy as np
from matplotlib import pyplot as plt


class Timed_Value:
    value: float
    time: Optional[float] = None

    def __init__(self, value: float, time: Optional[float] = None) -> None:
        self.value = value
        self.time = time


class PID:

    set_point: float
    controller_gain: float
    tauI: float
    tauD: float
    controller_output_zero: float

    _error_list: List[Timed_Value]
    _error_integral: float

    _process_variable_list: List[float]
    _derivative_process_variable: float

    def __init__(
        self,
        set_point,
        controller_gain: float,
        tauI: float,
        tauD: float,
        controller_output_zero: float,
    ) -> None:

        self.set_point = set_point
        self.controller_gain = controller_gain

        # Integral time constant, reset time
        self.tauI = tauI

        # Derivative time constant
        self.tauD = tauD

        self.controller_output_zero = controller_output_zero

        self._error_list = []
        self._error_integral = 0
        self._process_variable_list = []
        self._derivative_process_variable = 0

    @property
    def error_list(self):
        return self._error_list

    @property
    def error_integral(self):
        return self._error_integral

    @property
    def process_variable_list(self):
        return self._process_variable_list

    @property
    def derivative_process_variable(self):
        return self._derivative_process_variable

    def add_error(self, value: Timed_Value):
        self._error_list.append(value)
        self._error_integral += value.value

    def add_process_variable(self, process_variable: float):
        process_variable_prev: float

        if len(self.process_variable_list) > 0:
            process_variable_prev = self.process_variable_list[-1]

            self._process_variable_list.append(process_variable)
            self._derivative_process_variable = process_variable - process_variable_prev
        else:
            self._derivative_process_variable = 0

    def pid_step(self, error: Timed_Value, process_variable: float) -> float:
        self.add_error(Timed_Value(error))
        self.add_process_variable(process_variable)

        return self.output_process

    @property
    def output_process(self) -> float:
        """This is the Output Process Variable that controls the
        PID algorithm

        Returns:
            float: Output Process Variable
        """
        return (
            self.controller_output_zero
            + (self.controller_gain * self.error_list[-1].value)
            + (self.controller_gain * self.error_integral / self.tauI)
            - (self.controller_gain * self.tauI * self.derivative_process_variable)
        )


if __name__ == "__main__":

    dBu4 = 1.27

    pid = PID(
        set_point=np.full(40, dBu4),
        controller_gain=15.0,
        tauI=2.0,
        tauD=1.0,
        controller_output_zero=0.0,
    )
