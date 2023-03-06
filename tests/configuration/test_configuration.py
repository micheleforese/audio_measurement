from pathlib import Path
from audio.config.sweep import SweepConfig


def test_configuration():
    file = Path(__file__).parent / "config.xml"
    config = SweepConfig.from_xml_file(file)
    config.print()

    file = Path(__file__).parent / "config.full.xml"
    config = SweepConfig.from_xml_file(file)
    config.print()
