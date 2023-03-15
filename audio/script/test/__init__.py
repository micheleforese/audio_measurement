import click

from audio.script.test.bk_precision import bk_precision
from audio.script.test.instrument import instrument
from audio.script.test.phase_analysis import phase_analysis
from audio.script.test.print_devices import print_devices


@click.group()
def test():
    pass


test.add_command(print_devices)
test.add_command(phase_analysis)
test.add_command(instrument)
test.add_command(bk_precision)
