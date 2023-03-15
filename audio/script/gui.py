import click

from audio.gui.rigol_admin import rigol_admin


@click.group()
def gui():
    pass


gui.add_command(rigol_admin)
