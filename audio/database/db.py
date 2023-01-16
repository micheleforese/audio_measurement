from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection
from typing import List, Optional

from audio.console import console


@dataclass
class DbChannel:
    sweep_id: int
    id: int
    name: str
    comment: Optional[str] = None


@dataclass
class DbSweep:
    sweep_id: int
    id: int
    name: str
    date: datetime
    comment: Optional[str]


@dataclass
class DbViewSweep(DbSweep):
    frequency_min: float
    frequency_max: float
    points_per_decade: float
    number_of_samples: int
    Fs_multiplier: float
    delay_measurements: float
    rms: float
    interpolation_rate: float


@dataclass
class DbFrequency:
    frequency: float
    Fs: float


class Database:
    connection: Connection
    _DATE_TIME_FORMAT: str = r"%Y-%m-%d %H:%M:%S.%f"

    def __init__(self, db_path: Path) -> None:
        self.connection = Connection(db_path)

    def create_database(self):

        cur = self.connection.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS test(
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                comment TEXT
            );

            CREATE TABLE IF NOT EXISTS sweep(
                test_id INTEGER NOT NULL,
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                comment TEXT,
                FOREIGN KEY(test_id) REFERENCES test(id)
            );

            CREATE TABLE IF NOT EXISTS frequency(
                sweep_id INTEGER,
                id INTEGER NOT NULL,
                frequency DOUBLE NOT NULL,
                Fs DOUBLE NOT NULL,
                FOREIGN KEY(sweep_id) REFERENCES sweep(id)
            );

            CREATE TABLE IF NOT EXISTS sweepVoltage(
                sweep_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                frequency_id INTEGER NOT NULL,
                id INTEGER NOT NULL,
                voltage DOUBLE NOT NULL,
                FOREIGN KEY(sweep_id) REFERENCES sweep(id),
                FOREIGN KEY(frequency_id) REFERENCES frequency(id),
                FOREIGN KEY(channel_id) REFERENCES channel(id)
            );

            CREATE TABLE IF NOT EXISTS sweepConfig(
                sweep_id INTEGER NOT NULL,
                frequency_min DOUBLE,
                frequency_max DOUBLE,
                points_per_decade DOUBLE,
                number_of_samples INT,
                Fs_multiplier DOUBLE,
                delay_measurements DOUBLE,
                rms DOUBLE,
                interpolation_rate DOUBLE,
                FOREIGN KEY(sweep_id) REFERENCES sweep(id)
            );

            CREATE TABLE IF NOT EXISTS channel(
                sweep_id INTEGER NOT NULL,
                id INTEGER NOT NULL,
                name TEXT NOT NULL,
                comment TEXT,
                FOREIGN KEY(sweep_id) REFERENCES sweep(id)
            );
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
        return cur.lastrowid

    def get_channels(self):
        cur = self.connection.cursor()
        data = cur.execute("SELECT * FROM channel").fetchall()
        channels = [DbChannel(ch[0], ch[1], ch[2], ch[3]) for ch in data]
        return channels

    def insert_frequency(
        self, sweep_id: int, frequency_id: int, frequency: float, Fs: float
    ):
        cur = self.connection.cursor()
        data = (sweep_id, frequency_id, frequency, Fs)
        cur.execute(
            f"""INSERT INTO frequency(sweep_id, id, frequency, Fs) VALUES ({",".join(["?"] * len(data))})""",
            data,
        )
        cur.close()
        self.connection.commit()
        return cur.lastrowid

    def insert_frequencies(
        self, sweep_id: int, frequencies: List[float], Fs: List[float]
    ):
        cur = self.connection.cursor()
        data = [
            (sweep_id, freq_id, freq_value, Fs)
            for freq_id, (freq_value, Fs) in enumerate(zip(frequencies, Fs))
        ]
        cur.executemany(
            f"""INSERT INTO frequency(sweep_id, id, frequency, Fs) VALUES ({",".join(["?"] * len(data[0]))})""",
            data,
        )
        cur.close()
        self.connection.commit()

    def get_frequencies(self, sweep_id: int):
        cur = self.connection.cursor()
        data = cur.execute(
            f"SELECT frequency, Fs FROM frequency WHERE sweep_id = {sweep_id} ORDER BY id ASC"
        ).fetchall()

        # channels = [DbChannel(ch[0], ch[1], ch[2], ch[3]) for ch in data]
        return [DbFrequency(freq[0], freq[1]) for freq in data]

    def insert_sweep(
        self, test_id: int, name: str, date: datetime, comment: Optional[str] = None
    ) -> int:
        cur = self.connection.cursor()
        data = (
            test_id,
            name,
            date.strftime(self._DATE_TIME_FORMAT),
            comment,
        )
        cur.execute(
            "INSERT INTO sweep(test_id, name, date, comment) VALUES (?,?,?,?)",
            data,
        )
        cur.close()
        self.connection.commit()
        return cur.lastrowid

    def get_sweeps(self):
        cur = self.connection.cursor()
        data = cur.execute(
            """
            SELECT * FROM sweep
            """
        ).fetchall()
        sweep = [
            DbSweep(
                sweep_id=sweep[0],
                id=sweep[1],
                name=sweep[2],
                date=datetime.strptime(sweep[3], self._DATE_TIME_FORMAT),
                comment=sweep[4],
            )
            for sweep in data
        ]
        return sweep

    def view_sweeps(self):
        cur = self.connection.cursor()
        data = cur.execute(
            """
            SELECT
                sweep.test_id,
                sweep.id,
                sweep.name,
                sweep.date,
                sweep.comment,
                sweepConfig.frequency_min,
                sweepConfig.frequency_max,
                sweepConfig.points_per_decade,
                sweepConfig.number_of_samples,
                sweepConfig.Fs_multiplier,
                sweepConfig.delay_measurements,
                sweepConfig.rms,
                sweepConfig.interpolation_rate
            FROM sweep
            LEFT JOIN sweepConfig ON sweepConfig.sweep_id = sweep.id
            """
        ).fetchall()
        sweep = [
            DbViewSweep(
                sweep_id=sweep[0],
                id=sweep[1],
                name=sweep[2],
                date=datetime.strptime(sweep[3], self._DATE_TIME_FORMAT),
                comment=sweep[4],
                frequency_min=sweep[5],
                frequency_max=sweep[6],
                points_per_decade=sweep[7],
                number_of_samples=sweep[8],
                Fs_multiplier=sweep[9],
                delay_measurements=sweep[10],
                rms=sweep[11],
                interpolation_rate=sweep[12],
            )
            for sweep in data
        ]
        return sweep

    def insert_test(self, name: str, date: datetime, comment: Optional[str] = None):
        cur = self.connection.cursor()
        data = (
            name,
            date.strftime(self._DATE_TIME_FORMAT),
            comment,
        )
        cur.execute(
            "INSERT INTO test(name, date, comment) VALUES (?,?,?)",
            data,
        )
        cur.close()
        self.connection.commit()
        return cur.lastrowid

    def insert_sweep_config(
        self,
        sweep_id: int,
        frequency_min: float,
        frequency_max: float,
        points_per_decade: float,
        number_of_samples: int,
        Fs_multiplier: float,
        delay_measurements: float,
        rms: float,
        interpolation_rate: float,
    ):
        cur = self.connection.cursor()
        data = (
            sweep_id,
            frequency_min,
            frequency_max,
            points_per_decade,
            number_of_samples,
            Fs_multiplier,
            delay_measurements,
            rms,
            interpolation_rate,
        )
        cur.execute(
            f"""INSERT INTO sweepConfig(
                sweep_id,
                frequency_min,
                frequency_max,
                points_per_decade,
                number_of_samples,
                Fs_multiplier,
                delay_measurements,
                rms,
                interpolation_rate
            ) VALUES ({",".join(["?"] * len(data))})
            """,
            data,
        )
        cur.close()
        self.connection.commit()

    def insert_sweep_voltage(
        self,
        sweep_id: int,
        channel_id: int,
        frequency_id: int,
        voltage_id: int,
        voltage: float,
    ):
        cur = self.connection.cursor()
        data = (sweep_id, channel_id, frequency_id, voltage_id, voltage)
        cur.execute(
            f"""
            INSERT INTO frequency(
                sweep_id,
                channel_id,
                frequency_id,
                id,
                frequency,
                Fs
            )
            VALUES ({",".join(["?"] * len(data))})""",
            data,
        )
        cur.close()
        self.connection.commit()

    def insert_sweep_voltages(
        self,
        sweep_id: int,
        channel_id: int,
        frequency_id: int,
        voltages: List[float],
    ):
        cur = self.connection.cursor()
        data = [
            (sweep_id, channel_id, frequency_id, volt_id, volt_value)
            for volt_id, volt_value in enumerate(voltages)
        ]
        cur.executemany(
            f"""
            INSERT INTO sweepVoltage(
                sweep_id,
                channel_id,
                frequency_id,
                id,
                voltage
            )
            VALUES ({",".join(["?"] * len(data[0]))})
            """,
            data,
        )
        cur.close()
        self.connection.commit()

    def get_sweep_voltages(
        self,
        sweep_id: int,
        channel_id: int,
        frequency_id: int,
    ):
        cur = self.connection.cursor()
        data = cur.execute(
            f"""
            SELECT voltage
            FROM sweepVoltage
            WHERE sweep_id = {sweep_id} 
            ORDER BY id ASC
            """
        ).fetchall()

        return data
