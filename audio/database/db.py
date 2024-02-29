from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Self

import mysql.connector
from mysql.connector.connection import MySQLConnection

from audio.console import console
from audio.constant import APP_DB_AUTH_PATH
import configparser

if TYPE_CHECKING:
    from mysql.connector.cursor import MySQLCursor


@dataclass
class DbTest:
    id_: int
    name: str
    date: datetime
    comment: str | None = None


@dataclass
class DbSweep:
    id_: int
    test_id: int
    name: str
    date: datetime
    comment: str | None = None


@dataclass
class DbFrequency:
    id_: int
    sweep_id: int
    idx: int
    frequency: float
    sampling_frequency: float


@dataclass
class DbChannel:
    id_: int
    sweep_id: int
    idx: int
    name: str
    comment: str | None = None


@dataclass
class DbSweepConfig:
    sweep_id: int
    amplitude: float | None
    frequency_min: float | None
    frequency_max: float | None
    points_per_decade: float | None
    number_of_samples: float | None
    sampling_frequency_multiplier: float | None
    delay_measurements: float | None


@dataclass
class DbSweepVoltage:
    id_: int
    frequency_id: int
    channel_id: int
    voltages: list[float]

class DatabaseConfig:
    host: str
    port: str
    user: str
    password: str

    def __init__(self, config_path: Path) -> None:
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create the file with default values
            with open(config_path, 'w') as f:
                default_config = """
[Database]
host = localhost
port = 3306
user = root
password = password
"""
                f.write(default_config)

        # Load configuration using configparser
        config = configparser.ConfigParser()
        config.read(config_path)

        # Read configuration values
        self.host = config.get("Database", "host")
        self.port = config.get("Database", "port")
        self.user = config.get("Database", "user")
        self.password = config.get("Database", "password")



class Database:
    connection: MySQLConnection
    _DATE_TIME_FORMAT: str = r"%Y-%m-%d %H:%M:%S.%f"

    def __init__(self: Self) -> None:
        try:
            db_config = DatabaseConfig(APP_DB_AUTH_PATH)
            console.print(db_config)
            self.connection = MySQLConnection(
                host=db_config.host,
                port=db_config.port,
                user=db_config.user,
                password=db_config.password,
            )
            if self.connection.is_connected():
                console.print("Connected to MySQL database")
        except mysql.connector.Error as err:
            console.log(err)

    def create_database(self: Self) -> None:
        file_create_database = Path(__file__).parent / "create_database.sql"

        cur = self.connection.cursor()
        try:
            cur.execute(file_create_database.read_text(), multi=True)
        except mysql.connector.errors.Error as err:
            console.log(err)
        self.connection.commit()

    def drop_database(self: Self) -> None:
        cur = self.connection.cursor()
        cur.execute("DROP DATABASE IF EXISTS audio")
        cur.execute("CREATE DATABASE audio")
        self.connection.commit()

    def insert_test(
        self: Self,
        name: str,
        date: datetime,
        comment: str | None = None,
    ) -> int | None:
        data = (name, date, comment)
        console.log(data)

        cur = self.connection.cursor()
        cur.execute(
            "INSERT INTO audio.test(name, date, comment) VALUES (%s,%s,%s)",
            data,
        )
        self.connection.commit()
        return cur.lastrowid

    def get_test(self: Self, test_id: int) -> DbTest:
        cur = self.connection.cursor()
        cur.execute(
            "SELECT id, name, date, comment FROM audio.test WHERE id = %s;",
            (test_id,),
        )
        data: tuple[int, str, str, str | None] = cur.fetchone()
        _id, name, date, comment = data
        return DbTest(
            id_=_id,
            name=name,
            date=datetime.strptime(date, self._DATE_TIME_FORMAT).astimezone(),
            comment=comment,
        )

    def insert_test_config(self: Self, test_id: int, config: str) -> int | None:
        cur = self.connection.cursor()
        data = (test_id, config.encode())
        cur.execute(
            """
            INSERT INTO audio.testConfig(
                test_id,
                config
            )
            VALUES (%s, %s)
            """,
            data,
        )
        self.connection.commit()
        return cur.lastrowid

    def insert_sweep(
        self: Self,
        test_id: int,
        name: str,
        date: datetime,
        comment: str | None = None,
    ) -> int | None:
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

    def get_all_sweeps(self: Self) -> list[DbSweep]:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute("SELECT * FROM audio.sweep")
        data: list[tuple[int, int, str, str, str | None]] = cur.fetchall()

        return [
            DbSweep(
                id_=_id,
                test_id=test_id,
                name=name,
                date=datetime.strptime(date, self._DATE_TIME_FORMAT).astimezone(),
                comment=comment,
            )
            for _id, test_id, name, date, comment in data
        ]

    def get_sweeps(self: Self, test_id: int) -> list[DbSweep]:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute("SELECT * FROM audio.sweep WHERE test_id = %s", (test_id,))
        data: tuple[int, int, str, str, str | None] = cur.fetchone()
        _id, test_id, name, date, comment = data

        return DbSweep(id_=_id, test_id=test_id, name=name, date=date, comment=comment)

    def get_sweep(self: Self, sweep_id: int) -> DbSweep:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute("SELECT * FROM audio.sweep WHERE sweep_id = %s", (sweep_id))
        data: tuple[int, int, str, str, str | None] = cur.fetchone()
        _id, test_id, name, date, comment = data
        return DbSweep(
            id_=_id,
            test_id=test_id,
            name=name,
            date=datetime.strptime(date, self._DATE_TIME_FORMAT).astimezone(),
            comment=comment,
        )

    def insert_frequency(
        self: Self,
        sweep_id: int,
        idx: int,
        frequency: float,
        sampling_frequency: float,
    ) -> int | None:
        cur: MySQLCursor = self.connection.cursor()
        data: tuple[int, int, float, float] = (
            sweep_id,
            idx,
            float(frequency),
            float(sampling_frequency),
        )
        cur.execute(
            """
            INSERT INTO audio.frequency(
                sweep_id,
                idx,
                frequency,
                Fs
            )
            VALUES (%s, %s, %s, %s)
            """,
            data,
        )
        self.connection.commit()
        return cur.lastrowid

    def get_frequencies_from_sweep_id(self: Self, sweep_id: int) -> list[DbFrequency]:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute(
            """
            SELECT
                id,
                sweep_id,
                idx,
                frequency,
                Fs
            FROM audio.frequency
            WHERE sweep_id = %s ORDER BY idx ASC
            """,
            (sweep_id,),
        )

        data: list[tuple[int, int, int, float, float]] = cur.fetchall()

        frequency_data: list[DbFrequency] = [
            DbFrequency(
                id_=_id,
                sweep_id=sweep_id,
                idx=idx,
                frequency=frequency,
                sampling_frequency=Fs,
            )
            for _id, sweep_id, idx, frequency, Fs in data
        ]

        return frequency_data

    def get_frequencies_from_id(self: Self, frequency_id: int) -> DbFrequency:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute(
            """
            SELECT
                id,
                sweep_id,
                idx,
                frequency,
                Fs,
                rms,
                rms_interpolation_rate
            FROM audio.frequency
            WHERE id = %s
            ORDER BY idx ASC
            """,
            (frequency_id,),
        )

        data: tuple[
            int,
            int,
            int,
            float,
            float,
            float,
            float,
        ] = cur.fetchone()
        (
            _id,
            sweep_id,
            idx,
            frequency,
            sampling_frequency,
            rms,
            rms_interpolation_rate,
        ) = data
        frequency_data: DbFrequency = DbFrequency(
            id_=_id,
            sweep_id=sweep_id,
            idx=idx,
            frequency=frequency,
            sampling_frequency=sampling_frequency,
            rms=rms,
            rms_interpolation_rate=rms_interpolation_rate,
        )

        return frequency_data

    def insert_channel(
        self: Self,
        sweep_id: int,
        idx: int,
        name: str,
        comment: str | None = None,
    ) -> int | None:
        cur: MySQLCursor = self.connection.cursor()
        data: tuple[int, int, str, str | None] = (sweep_id, idx, name, comment)
        cur.execute(
            "INSERT INTO audio.channel(sweep_id, idx, name, comment) VALUES (%s, %s, %s, %s)",
            data,
        )
        self.connection.commit()
        return cur.lastrowid

    def get_channels_from_sweep_id(self: Self, sweep_id: int) -> list[DbChannel]:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute("SELECT * FROM audio.channel WHERE sweep_id = %s", (sweep_id,))

        data: list[tuple[int, int, int, str, str | None]] = cur.fetchall()

        channels_data: list[DbChannel] = [
            DbChannel(id_=_id, sweep_id=sweep_id, idx=idx, name=name, comment=comment)
            for _id, sweep_id, idx, name, comment in data
        ]
        return channels_data

    def get_channel_from_id(self: Self, channel_id: int) -> DbChannel:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute("SELECT * FROM audio.channel WHERE id = %s", (channel_id,))
        data: tuple[int, int, int, str, str | None] = cur.fetchone()

        _id, sweep_id, idx, name, comment = data

        return DbChannel(
            id_=_id,
            sweep_id=sweep_id,
            idx=idx,
            name=name,
            comment=comment,
        )

    def insert_sweep_config_data(self: Self, data: DbSweepConfig) -> int | None:
        cur: MySQLCursor = self.connection.cursor()
        data: tuple[
            int,
            float | None,
            float | None,
            float | None,
            float | None,
            int | None,
            float | None,
            float | None,
        ] = (
            data.sweep_id,
            float(data.amplitude),
            float(data.frequency_min),
            float(data.frequency_max),
            float(data.points_per_decade),
            data.number_of_samples,
            float(data.sampling_frequency_multiplier),
            float(data.delay_measurements),
        )
        cur.execute(
            """
            INSERT INTO audio.sweepConfig(
                sweep_id,
                amplitude,
                frequency_min,
                frequency_max,
                points_per_decade,
                number_of_samples,
                Fs_multiplier,
                delay_measurements
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            data,
        )
        self.connection.commit()
        return cur.lastrowid

    def get_sweep_config(self: Self, sweep_id: int) -> DbSweepConfig:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute(
            """
            SELECT * FROM audio.sweepConfig WHERE sweep_id = %s
            """,
            (sweep_id,),
        )
        data: tuple[
            int,
            float | None,
            float | None,
            float | None,
            float | None,
            int,
            float | None,
            float | None,
        ] = cur.fetchone()

        (
            sweep_id,
            amplitude,
            frequency_min,
            frequency_max,
            points_per_decade,
            number_of_samples,
            sampling_frequency_multiplier,
            delay_measurements,
        ) = data

        return DbSweepConfig(
            sweep_id=sweep_id,
            amplitude=amplitude,
            frequency_min=frequency_min,
            frequency_max=frequency_max,
            points_per_decade=points_per_decade,
            number_of_samples=number_of_samples,
            sampling_frequency_multiplier=sampling_frequency_multiplier,
            delay_measurements=delay_measurements,
        )

    def insert_sweep_voltages(
        self: Self,
        frequency_id: int,
        channel_id: int,
        voltages: list[float],
    ) -> int | None:
        cur: MySQLCursor = self.connection.cursor()
        voltages_string: str = "\n".join([str(v) for v in voltages])
        data: tuple[int, int, bytes] = (
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
        self.connection.commit()
        return cur.lastrowid

    def get_sweep_voltages_from_id(
        self: Self,
        sweep_voltages_id: int,
    ) -> DbSweepVoltage:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute(
            """
            SELECT *
            FROM audio.sweepVoltage
            WHERE id = %s
            ORDER BY id ASC
            """,
            (sweep_voltages_id),
        )
        data: tuple[int, int, int, bytes] = cur.fetchone()
        _id, _frequency_id, _channel_id, _voltages = data
        voltages: list[float] = [
            float(line) for line in _voltages.decode().splitlines()
        ]
        sweep_voltages_data: DbSweepVoltage = DbSweepVoltage(
            id_=_id,
            frequency_id=_frequency_id,
            channel_id=_channel_id,
            voltages=voltages,
        )
        return sweep_voltages_data

    def get_sweep_voltages(
        self: Self,
        frequency_id: int,
        channel_id: int,
    ) -> DbSweepVoltage:
        cur: MySQLCursor = self.connection.cursor()
        cur.execute(
            """
            SELECT *
            FROM audio.sweepVoltage
            WHERE frequency_id = %s AND channel_id = %s
            """,
            (frequency_id, channel_id),
        )
        data: tuple[int, int, int, bytes] = cur.fetchone()

        _id, _frequency_id, _channel_id, _voltages = data
        voltages: list[float] = [
            float(volt) for volt in _voltages.decode().splitlines()
        ]
        return DbSweepVoltage(
            id_=_id,
            frequency_id=_frequency_id,
            channel_id=_channel_id,
            voltages=voltages,
        )
