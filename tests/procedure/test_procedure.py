from audio.procedure import Procedure
from pathlib import Path
from audio.console import console


def test_procedure():
    file = Path(__file__).parent / "la_125.xml"
    proc = Procedure.from_xml_file(file)
    proc.print()
