import click

from audio.script.generator import generator
from audio.script.gui import gui
from audio.script.ni import ni
from audio.script.plot import plot
from audio.script.procedure import procedure
from audio.script.rigol import rigol
from audio.script.set_level import set_level
from audio.script.solar import (
    find_max_power,
    lux,
    lux_find,
    lux_set,
    panel_characterization,
    solar,
)
from audio.script.sweep import sweep
from audio.script.sweep_debug import sweep_debug
from audio.script.test import test
from audio.procedure.analysis import analysis, balanced_analysis


@click.group()
def cli() -> None:
    """This is the CLI for the audio measurements tools"""


cli.add_command(sweep)
cli.add_command(sweep_debug)
cli.add_command(plot)
cli.add_command(set_level)
cli.add_command(procedure)

# Devices
cli.add_command(rigol)
cli.add_command(ni)

# GUI
cli.add_command(gui)

# Test Commands
cli.add_command(test)

# Solar Panels
cli.add_command(solar)
cli.add_command(lux)
cli.add_command(lux_set)
cli.add_command(lux_find)
cli.add_command(find_max_power)
cli.add_command(panel_characterization)

# Generator
cli.add_command(generator)

@click.group()
def audio() -> None:
    """CLI for Audio Application"""

cli.add_command(audio)

audio.add_command(analysis)
audio.add_command(balanced_analysis)