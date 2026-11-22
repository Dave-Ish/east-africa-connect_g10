"""MySQL connection helpers for East Africa Connect's terminal application.

Install the driver with: python -m pip install -r requirements.txt
Configure MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, and
MYSQL_DATABASE in the environment. For Aiven, also set MYSQL_SSL_CA to the
path of the downloaded Aiven CA certificate.
"""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

SCHEMA_PATH = Path(__file__).resolve().with_name("schema.sql")
_DATABASE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
DEFAULT_DATABASE = "east_africa_connect"


def _mysql_connector() -> Any:
    """Import the driver lazily and give a helpful setup message if missing."""
    try:
        import mysql.connector
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "MySQL driver is not installed. Run: "
            "python -m pip install -r requirements.txt"
        ) from exc
    return mysql.connector


def _config(include_database: bool = True) -> dict[str, Any]:
    """Read MySQL settings from environment variables, never from source code."""
    user = os.getenv("MYSQL_USER")
    if not user:
        raise RuntimeError("Set MYSQL_USER in the environment before connecting to MySQL.")

    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    ca_value = os.getenv("MYSQL_SSL_CA")
    is_local = host.lower() in {"localhost", "127.0.0.1", "::1"}
    if not is_local and not ca_value:
        raise RuntimeError("Set MYSQL_SSL_CA to the Aiven CA certificate path for remote MySQL.")

    config: dict[str, Any] = {
        "host": host,
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": user,
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "connection_timeout": 10,
        "autocommit": False,
    }
    if ca_value:
        ca_path = Path(ca_value).expanduser().resolve()
        if not ca_path.is_file():
            raise FileNotFoundError(f"MySQL CA certificate was not found: {ca_path}")
        config["ssl_ca"] = str(ca_path)
        config["ssl_verify_cert"] = True
        config["ssl_verify_identity"] = True
    if include_database:
        config["database"] = os.getenv("MYSQL_DATABASE", DEFAULT_DATABASE)
    return config


def get_connection() -> Any:
    """Return an open MySQL connection; the caller is responsible for closing it."""
    return _mysql_connector().connect(**_config(include_database=True))


@contextmanager
def db_session() -> Iterator[Any]:
    """Yield a MySQL connection, commit on success, roll back on error, then close."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> str:
    """Apply db/schema.sql to the selected database, which must already exist.

    Create/select the database in Aiven Console first. The service user needs
    permission to create tables and indexes inside that database.
    """
    database = os.getenv("MYSQL_DATABASE", DEFAULT_DATABASE)
    if not _DATABASE_NAME_PATTERN.fullmatch(database):
        raise ValueError("MYSQL_DATABASE may contain only letters, numbers, and underscores.")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = [statement.strip() for statement in schema_sql.split(";") if statement.strip()]
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            for statement in statements:
                cursor.execute(statement)
        finally:
            cursor.close()
    return database
