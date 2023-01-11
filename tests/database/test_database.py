import os
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection

import numpy as np
import pandas as pd
import xarray as xr

from audio.console import console
from audio.database.db import Database
from audio.utility.timer import Timer


def test_database():

    HOME = Path(__file__).parent

    file_database = HOME / "data.db"
    # os.remove(file_database)
    db = Database(file_database)
    db.create_database()

    # SWEEP
    sweep_id = db.insert_sweep(
        "Sweep bello", datetime.now(), comment="Uno a caso per prova"
    )
    sweeps = db.get_sweeps()

    console.print(sweeps)
    console.print(sweep_id)

    # CHANNEL
    db.insert_channel(sweep_id, 0, "cDAQ9189-1CDBE0AMod5/ai0")
    db.insert_channel(sweep_id, 1, "cDAQ9189-1CDBE0AMod5/ai1", "Commento bello")
    db.insert_channel(sweep_id, 2, "cDAQ9189-1CDBE0AMod5/ai2")
    channels = db.get_channels()
    console.print(channels)
