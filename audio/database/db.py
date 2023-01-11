from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection
from typing import Optional

from audio.console import console


@dataclass
class DbChannel:
    sweep_id: int
    id: int
    name: str
    comment: Optional[str] = None


@dataclass
class DbSweep:
    id: int
    name: str
    date: datetime
    comment: Optional[str] = None


class Database:
    connection: Connection
    _DATE_TIME_FORMAT: str = r"%Y-%m-%d %H:%M:%S.%f"

    def __init__(self, db_path: Path) -> None:
        self.connection = Connection(db_path)

    def create_database(self):

        cur = self.connection.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS frequency(
                sweep_id INTEGER,
                id INTEGER NOT NULL,
                frequency DOUBLE NOT NULL,
                FOREIGN KEY(sweep_id) REFERENCES sweep(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sweep(
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                comment TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS test(
                id INTEGER NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                comment TEXT,
                date TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sweepVoltage(
                frequency_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                id INTEGER NOT NULL,
                voltage DOUBLE NOT NULL,
                FOREIGN KEY(frequency_id) REFERENCES frequency(id),
                FOREIGN KEY(channel_id) REFERENCES channel(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sweepConfig(
                frequency_id INTEGER NOT NULL,
                rms DOUBLE NOT NULL,
                dBV DOUBLE NOT NULL,
                Fs DOUBLE NOT NULL,
                number_of_samples INTEGER NOT NULL,
                FOREIGN KEY(frequency_id) REFERENCES frequency(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS channel(
                sweep_id INTEGER NOT NULL,
                id INTEGER NOT NULL,
                name TEXT NOT NULL,
                comment TEXT,
                FOREIGN KEY(sweep_id) REFERENCES sweep(id)
            )
            """
        )
        cur.close()
        self.connection.commit()

    def insert_channel(
        self, sweep_id: int, channel_id: int, name: str, comment: Optional[str] = None
    ):
        cur = self.connection.cursor()
        data = (sweep_id, channel_id, name, comment)
        cur.execute(
            "INSERT INTO channel(sweep_id, id, name, comment) VALUES (?,?,?,?)", data
        )
        cur.close()
        self.connection.commit()

    def get_channels(self):
        cur = self.connection.cursor()
        data = cur.execute("SELECT * FROM channel").fetchall()
        channels = [DbChannel(ch[0], ch[1], ch[2], ch[3]) for ch in data]
        return channels

    def insert_frequency(self, sweep_id: int, frequency_id: int, frequency: float):
        cur = self.connection.cursor()
        data = (sweep_id, frequency_id, frequency)
        cur.execute(
            "INSERT INTO frequency(sweep_id, id, frequency) VALUES (?,?,?)",
            data,
        )
        cur.close()
        self.connection.commit()

    def insert_sweep(
        self, name: str, date: datetime, comment: Optional[str] = None
    ) -> int:
        cur = self.connection.cursor()
        data = (
            name,
            date.strftime(self._DATE_TIME_FORMAT),
            comment,
        )
        cur.execute(
            "INSERT INTO sweep(name, date, comment) VALUES (?,?,?)",
            data,
        )
        cur.close()
        self.connection.commit()
        return cur.lastrowid

    def get_sweeps(self):
        cur = self.connection.cursor()
        data = cur.execute("SELECT * FROM sweep").fetchall()
        sweep = [
            DbSweep(
                sweep[0],
                sweep[1],
                datetime.strptime(sweep[2], self._DATE_TIME_FORMAT),
                sweep[3],
            )
            for sweep in data
        ]
        return sweep
