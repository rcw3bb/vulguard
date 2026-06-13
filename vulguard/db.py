"""
vulguard.db - SQLite persistence layer for vulguard inspection sessions.

Provides functions to initialise the database, insert per-file inspection
records, query results by session, and delete records after report generation.

The default database location is ``~/.vulguard/vulguard.db``.  A custom
directory can be supplied to override the default.

:author: Ron Webb
:since: 1.1.0
"""

import sqlite3
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

_DB_NAME = "vulguard.db"
_DEFAULT_DIR = Path.home() / ".vulguard"


def get_db_path(db_dir: str | None = None) -> str:
    """Returns the absolute path to the vulguard SQLite database file.

    Uses *db_dir* when provided, otherwise falls back to ``~/.vulguard``.

    :param db_dir: Optional directory that overrides the default location.
    :return: Absolute path to the ``vulguard.db`` file.
    """
    directory = Path(db_dir) if db_dir else _DEFAULT_DIR
    return str(directory.resolve() / _DB_NAME)


@contextmanager
def _connect(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Context manager that opens and closes a SQLite connection.

    :param db_path: Absolute path to the database file.
    :yields: An open :class:`sqlite3.Connection`.
    """
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    """Creates the parent directory and the ``inspections`` table if absent.

    :param db_path: Absolute path to the database file.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                id          TEXT PRIMARY KEY,
                session_id  TEXT NOT NULL,
                file_path   TEXT NOT NULL,
                severity    TEXT NOT NULL,
                details     TEXT NOT NULL
            )
            """)
        conn.commit()


def insert_result(
    db_path: str,
    session_id: str,
    file_path: str,
    severity: str,
    details: str,
) -> None:
    """Inserts a single file inspection result into the database.

    A new UUID is generated automatically and used as the record's primary key.

    :param db_path: Absolute path to the database file.
    :param session_id: UUID string identifying the current inspection run.
    :param file_path: Absolute path to the inspected file.
    :param severity: Severity level (``CRITICAL``, ``MAJOR``, ``MINOR``, or ``NONE``).
    :param details: Human-readable description of the finding.
    """
    record_id = str(uuid.uuid4())
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO inspections (id, session_id, file_path, severity, details) "
            "VALUES (?, ?, ?, ?, ?)",
            (record_id, session_id, file_path, severity, details),
        )
        conn.commit()


def get_results_by_session(
    db_path: str,
    session_id: str,
) -> list[dict[str, str]]:
    """Returns all inspection records for a given session as a list of dicts.

    :param db_path: Absolute path to the database file.
    :param session_id: UUID string identifying the inspection run.
    :return: List of dicts with ``file``, ``severity``, and ``details`` keys,
             ordered by file path.
    """
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT file_path, severity, details FROM inspections "
            "WHERE session_id = ? ORDER BY file_path",
            (session_id,),
        )
        return [
            {"file": row[0], "severity": row[1], "details": row[2]}
            for row in cursor.fetchall()
        ]


def delete_results_by_session(db_path: str, session_id: str) -> None:
    """Deletes all inspection records associated with a session UUID.

    :param db_path: Absolute path to the database file.
    :param session_id: UUID string identifying the inspection run to remove.
    """
    with _connect(db_path) as conn:
        conn.execute(
            "DELETE FROM inspections WHERE session_id = ?",
            (session_id,),
        )
        conn.commit()
