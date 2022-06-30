from typing import List, Optional

import numpy as np


class Timed_Value:
    value: float
    time: Optional[float] = None

    def __init__(self, value: float, time: Optional[float] = None) -> None:
        self.value = value
        self.time = time


class PID_TERM:

    _proportional: List[float]
    _integral: List[float]
    _derivative: List[float]

    def __init__(self) -> None:
        self._proportional = [0]
        self._integral = [0]
        self._derivative = [0]

    @property
    def proportional(self):
        return self._proportional

    @property
    def integral(self):
        return self._integral

    @property
    def derivative(self):
        return self._derivative

    def add_proportional(self, value: float):
        self._proportional.append(value)

    def add_integral(self, value: float):
        self._integral.append(value)

    def add_derivative(self, value: float):
        self._derivative.append(value)


class PID_Controller:

    term: PID_TERM

    set_point: float
    controller_gain: float
    tauI: float
    tauD: float
    controller_output_zero: float

    _error_list: List[Timed_Value]  #
    _error_integral: float
    _error_integral_cache_index: int

    _process_output_list: List[float]  #
    _process_variable_list: List[float]

    def __init__(
        self,
        set_point,
        controller_gain: float,
        tauI: float,
        tauD: float,
        controller_output_zero: float,
    ) -> None:

        self.term = PID_TERM()

        self.set_point = set_point
        self.controller_gain = controller_gain

        # Integral time constant, reset time
        self.tauI = tauI

        # Derivative time constant
        self.tauD = tauD

        self.controller_output_zero = controller_output_zero

        self._error_integral_cache_index = 0

        self._error_list = []
        self._error_integral_list = [0]
        self._error_integral = 0

        self._process_variable_list = []
        self._derivative_process_variable_list = [0]
        self._derivative_process_variable = 0

        self._process_output_list = [controller_output_zero]

    @property
    def process_output_list(self):
        return self._process_output_list

    def add_process_output(self, value: float):
        self._process_output_list.append(value)

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

    def add_error(self, error: Timed_Value):
        self._error_list.append(error)

    def add_process_variable(self, process_variable: float):
        self._process_variable_list.append(process_variable)

    @staticmethod
    def check_limit_diff(error, lim):
        return abs(error) < lim

    @property
    def proportional_term(self) -> float:
        if len(self.error_list) > 0:
            return self.controller_gain * self.error_list[-1].value
        else:
            return 0

    @property
    def integral_term(self) -> float:
        # index_error_list = len(self._error_list)

        # if index_error_list > self._error_integral_cache_index:
        #     self._error_integral += calculate_area(
        #         self._error_list[self._error_integral_cache_index :]
        #     )
        #     self._error_integral_cache_index = index_error_list

        return (
            self.controller_gain
            * calculate_area([error.value for error in self.error_list])
            / self.tauI
        )

    @property
    def derivative_term(self) -> float:
        gradient = calculate_gradient(self.process_variable_list)
        return -self.controller_gain * self.tauD * gradient

    @property
    def output_process(self) -> float:
        """This is the Output Process Variable that controls the
        PID algorithm

        Returns:
            float: Output Process Variable
        """
        return (
            self.controller_output_zero
            + self.term.proportional[-1]
            + self.term.integral[-1]
            + self.term.derivative[-1]
        )


def calculate_area(function: List[float]) -> float:
    if len(function) > 1:
        return float(np.trapz(function))
    else:
        return 0


def calculate_gradient(function: List[float]) -> float:

    if len(function) > 1:
        return float(np.gradient(function)[-1])
    else:
        return 0


if __name__ == "__main__":

    dBu4 = 1.27

    pid = PID_Controller(
        set_point=np.full(40, dBu4),
        controller_gain=15.0,
        tauI=2.0,
        tauD=1.0,
        controller_output_zero=0.0,
    )
