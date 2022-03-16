from time import sleep
import pytest
from pathlib import Path
from cDAQ.config import Config
from cDAQ.console import console

from cDAQ.utility import cDAQ
import os


def test_config():
    config_obj: Config = Config()

    config: Path = Path(
        Path(__file__).absolute().parent.parent / "config" / "config_template.json5"
    )

    console.print(config)

    config_file = config.absolute()
    config_obj.from_file(config_file)

    config_obj.print()
