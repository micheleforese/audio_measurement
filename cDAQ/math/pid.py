from time import time
from gekko import GEKKO
import numpy as np
import matplotlib.pyplot as plt


gekko = GEKKO()
time_finish = 40

gekko.time = np.linspace(0, time_finish, 2 * time_finish + 1)

step = np.zeros(2 * time_finish + 1)

step[3:time_finish] = 2.0
step[time_finish:] = 5.0

# PID CONTROLLER MODEL

controller_gain: float = 15.0

# Integral time constant, reset time
tauI: float = 2.0

# Derivative time constant
tauD: float = 1.0

controller_output_bias: float = 0.0

controller_output = gekko.Var(value=0)

# The actual value
process_variable = gekko.Var(value=0)

# The point that we would like to reach
set_point: float = gekko.Param(value=step)


integral = gekko.Var(value=0)

error = gekko.Intermediate(set_point - process_variable)

gekko.Equation(integral.dt() == error)
gekko.Equation(controller_output == controller_output_bias)


class PID:

    step
    controller_gain: float

    def __init__(
        self,
        step,
        controller_gain,
        tauI: float,
        tauD: float,
        controller_output_zero: float,
    ) -> None:

        self.step = step
        self.controller_gain: float = controller_gain

        # Integral time constant, reset time
        self.tauI: float = tauI

        # Derivative time constant
        self.tauD: float = tauD

        self.controller_output_zero: float = controller_output_zero

    def integral_error(self, error, error_prev, dt):
        return (error + error_prev) * dt / 2

    def derivative_process_value(process_variable, process_variable_prev, dt):
        return (process_variable - process_variable_prev) / dt

    def output_process(self, error, integral_error, derivative_process_value):
        return (
            self.controller_output_zero
            + (self.controller_gain * error)
            + (self.controller_gain * integral_error / self.tauI)
            - (self.controller_gain * self.tauI * derivative_process_value)
        )


if __name__ == "__main__":

    dBu4 = 1.27

    pid = PID(
        step=np.full(40, dBu4),
        controller_gain=15.0,
        tauI=2.0,
        tauD=1.0,
        controller_output_zero=0.0,
    )
