import click

from audio.script.gui import gui
from audio.script.ni import ni
from audio.script.plot import plot
from audio.script.procedure import procedure
from audio.script.rigol import rigol
from audio.script.set_level import set_level
from audio.script.sweep import sweep
from audio.script.sweep_debug import sweep_debug
from audio.script.test import test


@click.group()
def cli():
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
