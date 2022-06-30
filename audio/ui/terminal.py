from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from audio.console import console

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
    TextColumn(
        " - Frequency: [bold green]{task.fields[frequency]} - RMS: {task.fields[rms]}"
    ),
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
