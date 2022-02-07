#!/usr/bin/env python3
from inspect import CO_ASYNC_GENERATOR
from time import time
from UsbTmc import *
from rich.console import Console
from typing import List
import matplotlib.pyplot as plt
from numpy.ma.core import log10, sqrt
from utility import *
import numpy as np
from rich import pretty
from rich.traceback import install
from rich.table import Table
pretty.install()
install(show_locals=True)


console = Console()


def plot_log_db(file_path: str = "test.csv", file_png_path: str = "test.png",
                number_voltages=1):
    csvfile = genfromtxt(file_path, delimiter=",")

    Vpp = 2.0
    frequencies = []
    voltages = []
    dBV = []

    for row in list(csvfile):
        frequencies.append(row[0])

        voltage_average = 0
        voltage_sum = 0

        for n in range(1, number_voltages + 1):
            voltage_sum += n

        voltage_average /= 4

        voltages.append((row[2] + row[3] + row[4])/3)
        dBV.append(20 * log10(row[1] * Vpp / (2 * sqrt(2))))

    plt.plot(frequencies, dBV)
    plt.xscale("log")
    plt.title("Frequency response graph")
    plt.xlabel("Frequency")
    plt.ylabel("Vout/Vin dB")
    # plt.yticks(np.arange(start=-10.0, stop=11.0, step=5.0))
    plt.savefig(file_png_path)

    # print(csvfile)


def plot_V_out_filter(csv_file_path: str = "v_out_filter.csv", png_graph_file_path: str = "v_out_filter.png",
                      min_Hz: np.float = 40, max_Hz: np.float = 10000, frequency_p: np.float = 5000,
                      points_for_decade: np.int = 100,
                      Vpp: np.float = 2.0, n=1):

    f = open(csv_file_path, "w")

    step: np.float = 1 / points_for_decade
    frequencies = []
    voltages_out = []
    dBV = []

    min_index: np.float = log10(min_Hz)
    max_index: np.float = log10(max_Hz)

    steps_sum = (points_for_decade * max_index) - \
        (points_for_decade * min_index)

    i = 0
    while i < steps_sum + 1:
        frequency = pow(10, min_index + i * step)

        V_in = Vpp / (2*sqrt(2))

        A = abs(1/sqrt(1+pow(frequency/frequency_p, 2 * n))) * \
            abs(1/sqrt(1+pow(frequency_p/frequency, 2 * n)))

        voltage_out_temp = V_in * A
        dBV_temp = 20 * log10(voltage_out_temp * Vpp / (2 * sqrt(2)))

        frequencies.append(frequency)
        voltages_out.append(voltage_out_temp)
        dBV.append(dBV_temp)

        f.write("{},{},{}\n".format(frequency, voltage_out_temp, dBV_temp))

        i += 1

    f.close()

    plt.plot(frequencies, voltages_out)
    plt.xscale("log")
    plt.title("Frequency to Voltage output RC Filter")
    plt.xlabel("Frequency")
    plt.ylabel("V output")
    plt.savefig(png_graph_file_path)


def plot_percentage_error(csv_expected_file_path: str, csv_result_file_path: str, csv_file_path, png_graph_file_path: str, debug: bool = False):
    csv_expected = np.genfromtxt(csv_expected_file_path, delimiter=",",
                                 dtype=[("Frequency", 'f8'), ('Voltage', 'f8'), ('dBV', 'f8')])
    csv_result = np.genfromtxt(csv_result_file_path, delimiter=",",
                               dtype=[("Frequency", 'f8'), ('Voltage', 'f8')])

    frequency: List[np.float] = []
    perc_error: List[np.float] = []

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Frequency")
    table.add_column("Expected Voltage")
    table.add_column("Result Voltage")
    table.add_column("Percentage Error")

    f = open(csv_file_path, "w")

    for expected, result in zip(csv_expected, csv_result):

        frequency_temp: np.float = expected[0]
        expected_temp: np.float = expected[1]
        approx_temp: np.float = result[1]

        perc_error_temp: np.float = percentage_error(
            exact=expected_temp,
            approx=approx_temp,
        )

        if(debug):
            table.add_row(f"{frequency_temp}",
                          f"{expected_temp}", f"{approx_temp}",
                          f"{perc_error_temp}")

        if(perc_error_temp > 100.0):
            perc_error_temp = 100

        frequency.append(frequency_temp)
        perc_error.append(perc_error_temp)
        f.write("{},{}\n".format(frequency_temp, perc_error_temp))

    if(debug):
        console.print(table)

    plt.xticks(np.arange(0, 100, step=10))
    plt.plot(frequency, perc_error)
    # plt.xscale("log")
    plt.title("Percentage error, Expected Voltage / Result Voltage")
    plt.xlabel("Frequency")
    plt.ylabel("Percentage error")
    plt.savefig(png_graph_file_path)


def plot_percentage_error_temp(csv_expected_file_path: str, csv_result_file_path: str, csv_file_path, png_graph_file_path: str, debug: bool = False):
    csv_expected = np.genfromtxt(csv_expected_file_path, delimiter=",",
                                 dtype=[("Frequency", 'f8'), ('Voltage', 'f8'), ('dBV', 'f8')])
    csv_result = np.genfromtxt(csv_result_file_path, delimiter=",",
                               dtype=[("Frequency", 'f8'), ('Voltage', 'f8')])

    frequency: List[np.float] = []
    perc_error: List[np.float] = []

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Frequency")
    table.add_column("Expected Voltage")
    table.add_column("Result Voltage")
    table.add_column("Percentage Error")

    f = open(csv_file_path, "w")

    for expected, result in zip(csv_expected, csv_result):

        frequency_temp: np.float = expected[0]
        expected_temp: np.float = 1 / sqrt(2)
        approx_temp: np.float = result[1]

        perc_error_temp: np.float = percentage_error(
            exact=expected_temp,
            approx=approx_temp,
        )

        if(debug):
            table.add_row(f"{frequency_temp}",
                          f"{expected_temp}", f"{approx_temp}",
                          f"{perc_error_temp}")

        if(perc_error_temp > 100.0):
            perc_error_temp = 100

        frequency.append(frequency_temp)
        perc_error.append(perc_error_temp)
        f.write("{},{}\n".format(frequency_temp, perc_error_temp))

    if(debug):
        console.print(table)

    plt.xticks(np.arange(0, 100, step=10))
    plt.plot(frequency, perc_error)
    # plt.xscale("log")
    plt.title("Percentage error, Expected Voltage / Result Voltage")
    plt.xlabel("Frequency")
    plt.ylabel("Percentage error")
    plt.savefig(png_graph_file_path)


# plot_percentage_error('data/v_out_filter.csv',
#                       'data/test_filter.csv', 'data/percentage_error.csv', 'data/percentage_error.png', debug=True)

# plot_V_out_filter(csv_file_path="data/v_out_filter.csv",
#                   png_graph_file_path="data/v_out_filter.png",
#                   min_Hz=40, max_Hz=10000,
#                   points_for_decade=100,
#                   Vpp=2,
#                   frequency_p=1000, n=12)

# test_filter(file_path="data/test_filter.csv",
#             csv_file_path="data/v_out_filter.csv",
#             min_Hz=40, max_Hz=10000,
#             points_for_decade=100,
#             time_report=True, debug=True)

# plot_log_db(file_path="data/test_filter.csv",
#             file_png_path="data/test_filter.png")


def diff_steps(file_path: str):

    csvfile = genfromtxt(file_path, delimiter=",", names=[
                         "Frequency", "Voltage"], dtype="f8,f8")

    list_f_v = list(csvfile)

    curr_v: float
    prev_v: float = float(list_f_v[0][1])
    diff_v: float = 0.0

    curr_f: float
    prev_f: float = float(list_f_v[0][0])

    table = Table(
        Column("Prev Frequency", justify="right"),
        Column("Curr Frequency", justify="right"),
        Column("Prev Voltage", justify="right"),
        Column("Curr Voltage", justify="right"),
        Column("Step Difference", justify="right"),
        show_header=True
    )

    for row in list_f_v:
        curr_f = float(row[0])
        curr_v = float(row[1])

        diff_v = curr_v - prev_v

        style_voltage = "green"

        if(diff_v < 0):
            style_voltage = "red"

        table.add_row("{}".format(prev_f),
                      "{}".format(curr_f),
                      "{}".format(prev_v),
                      "{}".format(curr_v),
                      "[{}]{}[/]".format(style_voltage, diff_v))

        prev_f = curr_f
        prev_v = curr_v

    console.print(table)


number = 20

csv_file = "data/filter/test_filter_{}.csv".format(number)
png_file = "data/filter/test_filter_{}.png".format(number)

test_sampling(csv_file, min_Hz=800, max_Hz=1800,
              points_for_decade=100,
              sample_number=20,
              time_report=True, debug=True,
              )

plot_log_db(csv_file, png_file, number_voltages=20)

diff_steps(csv_file)

console.print("Finished")
