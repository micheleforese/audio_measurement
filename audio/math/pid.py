from typing import Literal, Self

import numpy as np


class TimedValue:
    value: float
    time: float | None = None

    def __init__(self: Self, value: float, time: float | None = None) -> None:
        self.value = value
        self.time = time


class PidTERM:
    _proportional: list[float]
    _integral: list[float]
    _derivative: list[float]

    def __init__(self: Self) -> None:
        self._proportional = [0]
        self._integral = [0]
        self._derivative = [0]

    @property
    def proportional(self: Self) -> list[float]:
        return self._proportional

    @property
    def integral(self: Self) -> list[float]:
        return self._integral

    @property
    def derivative(self: Self) -> list[float]:
        return self._derivative

    def add_proportional(self: Self, value: float) -> None:
        self._proportional.append(value)

    def add_integral(self: Self, value: float) -> None:
        self._integral.append(value)

    def add_derivative(self: Self, value: float) -> None:
        self._derivative.append(value)


class PidController:
    term: PidTERM

    set_point: float
    controller_gain: float
    tau_integral: float
    tau_derivative: float
    controller_output_zero: float

    _error_list: list[TimedValue]
    _error_integral: float
    _error_integral_cache_index: int

    _process_output_list: list[float]
    _process_variable_list: list[float]

    _derivative_process_variable_list: list[int]
    _derivative_process_variable: int

    def __init__(
        self: Self,
        set_point: float,
        controller_gain: float,
        tau_integral: float,
        tau_derivative: float,
        controller_output_zero: float,
    ) -> None:
        self.term = PidTERM()

        self.set_point = set_point
        self.controller_gain = controller_gain

        # Integral time constant, reset time
        self.tau_integral = tau_integral

        # Derivative time constant
        self.tau_derivative = tau_derivative

        self.controller_output_zero = controller_output_zero

        self._error_integral_cache_index = 0

        self._error_list = []
        self._error_integral_list: list[int] = [0]
        self._error_integral = 0

        self._process_variable_list = []
        self._derivative_process_variable_list = [0]
        self._derivative_process_variable = 0

        self._process_output_list = [controller_output_zero]

    @property
    def process_output_list(self: Self) -> list[float]:
        return self._process_output_list

    def add_process_output(self: Self, value: float) -> None:
        self._process_output_list.append(value)

    @property
    def error_list(self: Self) -> list[TimedValue]:
        return self._error_list

    @property
    def error_integral(self: Self) -> float:
        return self._error_integral

    @property
    def process_variable_list(self: Self) -> list[float]:
        return self._process_variable_list

    @property
    def derivative_process_variable(self: Self) -> int:
        return self._derivative_process_variable

    def add_error(self: Self, error: TimedValue) -> None:
        self._error_list.append(error)

    def add_process_variable(self: Self, process_variable: float) -> None:
        self._process_variable_list.append(process_variable)

    @staticmethod
    def check_limit_diff(error: float, lim: float) -> bool:
        return abs(error) < lim

    @property
    def proportional_term(self: Self) -> float:
        if len(self.error_list) < 0:
            return 0

        return self.controller_gain * self.error_list[-1].value

    @property
    def integral_term(self: Self) -> float:
        # if index_error_list > self._error_integral_cache_index:
        #     self._error_integral += calculate_area(

        return (
            self.controller_gain
            * calculate_area([error.value for error in self.error_list])
            / self.tau_integral
        )

    @property
    def derivative_term(self: Self) -> float:
        gradient: float = calculate_gradient(self.process_variable_list)
        return -self.controller_gain * self.tau_derivative * gradient

    @property
    def output_process(self: Self) -> float:
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


def calculate_area(function: list[float]) -> float:
    if len(function) < 1:
        return 0

    return float(np.trapz(function))


def calculate_gradient(samples: list[float]) -> float:
    if len(samples) < 2:
        return 0
    return float(np.gradient(samples)[-1])


if __name__ == "__main__":
    dbu4: float = 1.27

    pid: PidController = PidController(
        set_point=np.full(40, dbu4),
        controller_gain=15.0,
        tau_integral=2.0,
        tau_derivative=1.0,
        controller_output_zero=0.0,
    )
