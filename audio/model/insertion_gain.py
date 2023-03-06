import pathlib


class InsertionGain:
    insertion_gain_dB: float

    def __init__(self, file: pathlib.Path) -> None:

        if not file.exists() or not file.is_file():
            raise Exception("File does not Exists.")

        self.insertion_gain_dB = float(file.read_text(encoding="utf-8"))
