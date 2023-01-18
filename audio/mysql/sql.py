from typing import Optional

import mysql.connector
import mysqlx
from mysql.connector.connection import MySQLConnection

session = mysqlx.get_session()

schema = session.get_schema("audio")

schema.get_table()


class mysqlxdev:
    @staticmethod
    def get_session(
        user: str,
        password: str,
        host: str,
        port: int,
        database: Optional[str] = None,
    ):
        session = Session(
            MySQLConnection(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
            )
        )
        return session


class Session:
    connection: MySQLConnection

    def __init__(self, connection: MySQLConnection) -> None:
        self.connection = connection

    def get_schema():
        pass
