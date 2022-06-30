from nidaqmx._task_modules.channels.ao_channel import AOChannel
from nidaqmx.system import System
from nidaqmx.system._collections.device_collection import DeviceCollection
from rich.panel import Panel
from rich.table import Column, Table
from rich.tree import Tree

from audio.console import console


class cDAQ:
    """
    Class for Initialize the nidaqmx driver connection
    """

    system: System

    def __init__(self) -> None:

        # Get the system instance for the nidaqmx-driver
        self.system = System.local()

    def print_driver_version(self, debug: bool = False):
        """Prints the Version for the nidaqmx driver

        Args:
            debug (bool): if true, prints the versions divided in a table
        """

        if not debug:
            console.print(
                Panel.fit(
                    "Version: [blue]{}[/].[blue]{}[/].[blue]{}[/]".format(
                        self.system.driver_version.major_version,
                        self.system.driver_version.minor_version,
                        self.system.driver_version.update_version,
                    )
                )
            )
        else:
            table = Table(
                Column(justify="left"),
                Column(justify="right"),
                title="cDAQ Driver info",
                show_header=False,
            )

            # Major Version
            table.add_row(
                "Major Version", "{}".format(self.system.driver_version.major_version)
            )

            # Minor Version
            table.add_row(
                "Minor Version", "{}".format(self.system.driver_version.minor_version)
            )

            # Update Version
            table.add_row(
                "Update Version", "{}".format(self.system.driver_version.update_version)
            )
            console.print(table)

    def _list_devices(self) -> DeviceCollection:
        """Returns the Device connected to the machine

        Returns:
            DeviceCollection: Device List
        """

        return self.system.devices

    def print_list_devices(self):
        """Prints the Devices connected to the machine"""

        table = Table(title="Device List")
        table.add_column("[yellow]Name[/]", justify="left", style="blue", no_wrap=True)

        for device in self._list_devices():
            table.add_row(device.name)
        console.print(table)


def print_supported_output_types(channel: AOChannel):
    supported_types: Tree = Tree(
        "[yellow]Supported Types[/]",
    )

    for t in channel.physical_channel.ao_output_types:
        supported_types.add(
            "[green]{}[/green]: [blue]{}[/blue]".format(t.name, int(t.value))
        )

    console.print(Panel.fit(supported_types))
