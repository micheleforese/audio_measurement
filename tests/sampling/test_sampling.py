import pytest
from unittest.mock import patch
from cDAQ.curva import curva
from pathlib import Path


class Test_Sampling:
    def test_curva(self):

        THIS_PATH = Path(__file__).parent

        curva(
            THIS_PATH / "basic.json",
            THIS_PATH / "basic.csv",
            THIS_PATH / "basic.png",
            debug=True,
        )
        
        assert 1 == 1
