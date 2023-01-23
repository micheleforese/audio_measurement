from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection
from typing import Any, List, Optional, Tuple

from audio.console import console


@dataclass
class DbTest:
    id: int
    name: str
    date: datetime
    comment: Optional[str] = None


@dataclass
class DbSweep:
    id: int
    test_id: int
    name: str
    date: datetime
    comment: Optional[str] = None


@dataclass
class DbFrequency:
    id: int
    sweep_id: int
    idx: int
    frequency: float
    Fs: float
    rms: float
    rms_interpolation_rate: float


@dataclass
class DbChannel:
    id: int
    sweep_id: int
    idx: int
    name: str
    comment: Optional[str] = None


@dataclass
class DbSweepConfig:
    sweep_id: int
    amplitude: Optional[float]
    frequency_min: Optional[float]
    frequency_max: Optional[float]
    points_per_decade: Optional[float]
    number_of_samples: Optional[float]
    Fs_multiplier: Optional[float]
    delay_measurements: Optional[float]


@dataclass
class DbSweepVoltage:
    id: int
    frequency_id: int
    channel_id: int
    voltages: List[float]


import mysql.connector
import mysqlx
from mysql.connector.connection import MySQLConnection
from mysqlx import Session


class Database:
    connection: Connection
    _DATE_TIME_FORMAT: str = r"%Y-%m-%d %H:%M:%S.%f"

    def __init__(self) -> None:
        try:
            self.connection = MySQLConnection(
                host="localhost",
                port=3306,
                user="root",
                password="acmesystems",
            )
        except mysql.connector.Error as err:
            console.log(err)

    def create_database(self):
        file_create_database = Path(__file__).parent / "create_database.sql"

        cur = self.connection.cursor()
        try:
            cur.execute(file_create_database.read_text(), multi=True)
        except mysql.connector.errors.Error as err:
            console.log(err)
        self.connection.commit()

    def drop_database(self):
        cur = self.connection.cursor()
        cur.execute("DROP DATABASE IF EXISTS audio")
        cur.execute("CREATE DATABASE audio")
        self.connection.commit()

    def insert_test(self, name: str, date: datetime, comment: Optional[str] = None):
        data = (name, date, comment)
        console.log(data)

        cur = self.connection.cursor()
        cur.execute(
            "INSERT INTO audio.test(name, date, comment) VALUES (%s,%s,%s)", data
        )
        self.connection.commit()
        return cur.lastrowid

    def get_test(self, test_id: int):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM audio.test WHERE id = {test_id};")
        data = cur.fetchone()

        return data

    def insert_test_config(self, test_id: int, config: str):
        cur = self.connection.cursor()
        data = (test_id, config.encode())
        cur.execute(
            f"""
            INSERT INTO audio.testConfig(
                test_id,
                config
            )
            VALUES ({",".join(["%s"] * len(data))})
            """,
            data,
        )
        self.connection.commit()

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
            "INSERT INTO audio.sweep(test_id, name, date, comment) VALUES (%s,%s,%s,%s)",
            data,
        )
        self.connection.commit()
        return cur.lastrowid

    def get_all_sweeps(self):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM audio.sweep")
        data = cur.fetchall()

        sweeps = [
            DbSweep(id=_id, test_id=test_id, name=name, date=date, comment=comment)
            for _id, test_id, name, date, comment in data
        ]
        return sweeps

    def get_sweeps(self, test_id: int):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM audio.sweep WHERE test_id = {test_id}")
        data = cur.fetchall()

        sweeps = [
            DbSweep(id=_id, test_id=test_id, name=name, date=date, comment=comment)
            for _id, test_id, name, date, comment in data
        ]
        return sweeps

    def get_sweep(self, sweep_id: int):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM audio.sweep WHERE sweep_id = {sweep_id}")
        data = cur.fetchone()
        _id, test_id, name, date, comment = data
        sweep = DbSweep(id=_id, test_id=test_id, name=name, date=date, comment=comment)
        return sweep

    def insert_frequency(
        self,
        sweep_id: int,
        idx: int,
        frequency: float,
        Fs: float,
    ):
        cur = self.connection.cursor()
        data = (
            sweep_id,
            idx,
            frequency,
            Fs,
        )
        cur.execute(
            f"""
            INSERT INTO audio.frequency(
                sweep_id,
                idx,
                frequency,
                Fs,
            )
            VALUES ({",".join(["%s"] * len(data))})
            """,
            data,
        )
        self.connection.commit()
        return cur.lastrowid

    def get_frequencies_from_sweep_id(self, sweep_id: int):
        cur = self.connection.cursor()
        data = cur.execute(
            f"""
            SELECT
                id,
                sweep_id,
                idx,
                frequency,
                Fs,
                rms,
                rms_interpolation_rate
            FROM audio.frequency
            WHERE sweep_id = {sweep_id} ORDER BY idx ASC
            """
        )

        data = cur.fetchall()

        frequency_data = [
            DbFrequency(
                id=id,
                sweep_id=sweep_id,
                idx=idx,
                frequency=frequency,
                Fs=Fs,
                rms=rms,
                rms_interpolation_rate=rms_interpolation_rate,
            )
            for id, sweep_id, idx, frequency, Fs, rms, rms_interpolation_rate in data
        ]

        return frequency_data

    def get_frequencies_from_id(self, frequency_id: int):
        cur = self.connection.cursor()
        data = cur.execute(
            f"""
            SELECT
                id,
                sweep_id,
                idx,
                frequency,
                Fs,
                rms,
                rms_interpolation_rate
            FROM audio.frequency
            WHERE id = {frequency_id} ORDER BY idx ASC
            """
        )

        data = cur.fetchone()
        _id, sweep_id, idx, frequency, Fs, rms, rms_interpolation_rate = data
        frequency_data = DbFrequency(
            id=_id,
            sweep_id=sweep_id,
            idx=idx,
            frequency=frequency,
            Fs=Fs,
            rms=rms,
            rms_interpolation_rate=rms_interpolation_rate,
        )

        return frequency_data

    def insert_channel(
        self, sweep_id: int, idx: int, name: str, comment: Optional[str] = None
    ):
        cur = self.connection.cursor()
        data = (sweep_id, idx, name, comment)
        cur.execute(
            f"INSERT INTO audio.channel(sweep_id, idx, name, comment) VALUES ({','.join(['%s'] * len(data))})",
            data,
        )
        self.connection.commit()
        return cur.lastrowid

    def get_channels_from_sweep_id(self, sweep_id: int):
        cur = self.connection.cursor()
        data = cur.execute(
            f"SELECT * FROM audio.channel WHERE sweep_id = {sweep_id}"
        ).fetchall()

        channels_data = [
            DbChannel(id=_id, sweep_id=sweep_id, idx=idx, name=name, comment=comment)
            for _id, sweep_id, idx, name, comment in data
        ]
        return channels_data

    def get_channel_from_id(self, channel_id: int):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM audio.channel WHERE id = {channel_id}")
        data = cur.fetchone()

        _id, sweep_id, idx, name, comment = data

        return DbChannel(id=_id, sweep_id=sweep_id, idx=idx, name=name, comment=comment)

    def insert_sweep_config(
        self,
        sweep_id: int,
        amplitude: Optional[float] = None,
        frequency_min: Optional[float] = None,
        frequency_max: Optional[float] = None,
        points_per_decade: Optional[float] = None,
        number_of_samples: Optional[int] = None,
        Fs_multiplier: Optional[float] = None,
        delay_measurements: Optional[float] = None,
    ):
        cur = self.connection.cursor()
        data = (
            sweep_id,
            amplitude,
            frequency_min,
            frequency_max,
            points_per_decade,
            number_of_samples,
            Fs_multiplier,
            delay_measurements,
        )
        cur.execute(
            f"""
            INSERT INTO audio.sweepConfig(
                sweep_id,
                amplitude,
                frequency_min,
                frequency_max,
                points_per_decade,
                number_of_samples,
                Fs_multiplier,
                delay_measurements
            ) VALUES ({",".join(["?"] * len(data))})
            """,
            data,
        )
        self.connection.commit()

    def get_sweep_config(self, sweep_id: int):
        cur = self.connection.cursor()
        cur.execute(
            f"""
            SELECT * FROM audio.sweepConfig WHERE sweep_id = {sweep_id}
            """
        )
        data = cur.fetchone()

        (
            sweep_id,
            amplitude,
            frequency_min,
            frequency_max,
            points_per_decade,
            number_of_samples,
            Fs_multiplier,
            delay_measurements,
        ) = data

        return DbSweepConfig(
            sweep_id=sweep_id,
            amplitude=amplitude,
            frequency_min=frequency_min,
            frequency_max=frequency_max,
            points_per_decade=points_per_decade,
            number_of_samples=number_of_samples,
            Fs_multiplier=Fs_multiplier,
            delay_measurements=delay_measurements,
        )

    def insert_sweep_voltages(
        self,
        frequency_id: int,
        channel_id: int,
        voltages: List[float],
    ):
        cur = self.connection.cursor()
        voltages_string = [str(v) for v in voltages]
        voltages_string = "\n".join(voltages_string)
        data = (
            frequency_id,
            channel_id,
            voltages_string.encode(),
        )

        cur.execute(
            """
            INSERT INTO audio.sweepVoltage(
                frequency_id,
                channel_id,
                voltages
            )
            VALUES (%s, %s, %s)
            """,
            data,
        )
        cur.close()
        self.connection.commit()
        return cur.lastrowid

    def get_sweep_voltages_from_id(
        self,
        sweep_voltages_id: int,
    ):
        cur = self.connection.cursor()
        cur.execute(
            f"""
            SELECT *
            FROM audio.sweepVoltage
            WHERE id = {sweep_voltages_id}
            ORDER BY id ASC
            """
        )
        data: Tuple[int, int, int, bytes] = cur.fetchone()
        _id, _frequency_id, _channel_id, _voltages = data
        _voltages = [float(line) for line in _voltages.decode().splitlines()]
        sweep_voltages_data = DbSweepVoltage(
            id=_id,
            frequency_id=_frequency_id,
            channel_id=_channel_id,
            voltages=_voltages,
        )
        return sweep_voltages_data

    def get_sweep_voltages(
        self,
        frequency_id: int,
        channel_id: int,
    ):
        cur = self.connection.cursor()
        data: Tuple[int, int, int, bytes] = cur.execute(
            f"""
            SELECT *
            FROM audio.sweepVoltage
            WHERE frequency_id = {frequency_id} AND channel_id = {channel_id}
            """
        ).fetchone()

        _id, _frequency_id, _channel_id, _voltages = data
        sweep_voltages_data = DbSweepVoltage(
            id=_id,
            frequency_id=_frequency_id,
            channel_id=_channel_id,
            voltages=_voltages.decode(),
        )

        return sweep_voltages_data
