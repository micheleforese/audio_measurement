from pathlib import Path

import mysql
import mysqlx
from mysqlx.statement import SqlStatement

HOME = Path(__file__).parent


def test_mysqlx_connection():
    # Connect to server on localhost
    session = mysqlx.get_session(
        {
            "host": "localhost",
            "port": 33060,
            "user": "root",
            "password": "acmesystems",
        }
    )

    file_create_database: Path = HOME / "create_database.sql"
    statements = file_create_database.read_text().split(";")
    for sql in statements:
        session.sql(sql).execute()
    session.commit()
    session.close()


if __name__ == "__main__":
    test_mysqlx_connection()
