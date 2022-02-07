import usbtmc
from usbtmc.usbtmc import Instrument


def percentage_error(exact: float, approx: float) -> float:
    return (abs(approx - exact)/exact)*100
