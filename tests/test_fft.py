import numpy as np
from matplotlib import pyplot as plt
from scipy.fft import fft, fftfreq, rfft, rfftfreq

from cDAQ.console import console


def generate_sine_wave(freq, amplitude, sample_rate, duration):
    x = np.linspace(0, duration, sample_rate * duration, endpoint=False)

    # 2pi because np.sin takes radians
    y = amplitude * np.sin((2 * np.pi) * freq * x)
    return (x, y)


def test_fft():

    FREQUENCY = 400

    OVER_SAMP_RATE = 6

    SAMPLE_RATE = FREQUENCY * OVER_SAMP_RATE
    DURATION = 5  # Seconds

    AMPLITUDE_PEAK = 2
    AMPLITUDE_PEAK_TO_PEAK = AMPLITUDE_PEAK * 2

    t, nice_tone = generate_sine_wave(FREQUENCY, AMPLITUDE_PEAK, SAMPLE_RATE, DURATION)

    # Number of samples in normalized_tone
    N = len(t)

    yf = fft(nice_tone)

    sum = 0
    for y in yf:
        sum += np.float_power(y, 2)

    rms: float = np.sqrt(sum) / N

    console.print(f"RMS: {np.absolute(rms)}")

    ###############################

    n_samp = len(nice_tone)
    voltages_fft = fft(nice_tone, n_samp, workers=-1)

    sum = 0

    for v in voltages_fft:
        sum += (np.abs(v) / n_samp) ** 2

    rms: float = np.sqrt(sum / n_samp)

    console.print(f"RMS: {np.absolute(rms)}")
