from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.prompt import Confirm
from rich.table import Column, Table
from cDAQ.console import console

progress_sweep = Progress(
    SpinnerColumn(),
    "•",
    TextColumn(
        "[bold blue]{task.description}",
        justify="right",
    ),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    "•",
    TimeElapsedColumn(),
    "•",
    MofNCompleteColumn(),
    TextColumn(" - Frequency: [bold green]{task.fields[frequency]}"),
    console=console,
    transient=True,
)

progress_task = Progress(
    SpinnerColumn(),
    "•",
    TextColumn(
        "[bold blue]{task.description}",
    ),
    transient=True,
)

progress_list_task = Progress(
    SpinnerColumn(),
    "•",
    TextColumn(
        "[bold blue]{task.description}[/] - [bold green]{task.fields[task]}[/]",
    ),
    transient=True,
)
