from pathlib import Path

import numpy as np
from rich import inspect

from audio.config.sweep import SweepConfigXML
from audio.console import console


def test_config():

    THIS_PATH = Path(__file__).parent

    file = THIS_PATH / "config_test.json5"

    config = SweepConfigXML.from_file(file)

    config.print()
