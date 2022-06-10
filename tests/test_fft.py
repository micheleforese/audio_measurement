import pathlib
import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
from scipy.fft import fft, fftfreq, rfft, rfftfreq
from rich.panel import Panel

from cDAQ.console import console


def generate_sine_wave(freq, amplitude, sample_rate, duration):
    x = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)

    # 2pi because np.sin takes radians
    y = amplitude * np.sin((2 * np.pi) * freq * x)
    return (x, y)


def test_fft():

    FREQUENCY = 0.9

    OVER_SAMP_RATE = 6

    SAMPLE_RATE = FREQUENCY * OVER_SAMP_RATE
    DURATION = 2  # Seconds

    AMPLITUDE_PEAK = 0.25
    AMPLITUDE_PEAK_TO_PEAK = AMPLITUDE_PEAK * 2

    t, nice_tone = generate_sine_wave(FREQUENCY, AMPLITUDE_PEAK, SAMPLE_RATE, DURATION)

    # Number of samples in normalized_tone
    N = len(t)

    yf = fft(nice_tone)

    sum = 0
    for y in yf:
        sum += np.float_power(y, 2)

    rms: float = np.absolute(np.sqrt(sum) / N)

    console.print("\n")
    console.print(Panel(f"RMS: {rms}"))
