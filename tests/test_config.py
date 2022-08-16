from pathlib import Path

from audio.config.sweep import SweepConfigXML


def test_config():

    THIS_PATH = Path(__file__).parent

    file = THIS_PATH / "config_test.json5"

    config = SweepConfigXML.from_file(file)

    config.print()
