"""
tests.test_db - Unit tests for vulguard.db (SQLite persistence layer).

:author: Ron Webb
:since: 1.1.0
"""

import os
import sqlite3
import tempfile
import uuid

from vulguard.db import (
    delete_results_by_session,
    get_db_path,
    get_results_by_session,
    init_db,
    insert_result,
)


class TestGetDbPath:
    """Tests for the get_db_path helper.

    :author: Ron Webb
    :since: 1.1.0
    """

    def test_default_path_ends_with_db_name(self) -> None:
        """get_db_path() ends with 'vulguard.db' when no dir is given."""
        path = get_db_path()
        assert path.endswith("vulguard.db")

    def test_default_path_under_dot_vulguard(self) -> None:
        """get_db_path() places the DB under a .vulguard directory by default."""
        path = get_db_path()
        assert ".vulguard" in path

    def test_custom_dir_used(self) -> None:
        """get_db_path() uses the supplied directory when provided."""
        with tempfile.TemporaryDirectory() as tmp:
            path = get_db_path(tmp)
            assert path == os.path.join(os.path.abspath(tmp), "vulguard.db")


class TestInitDb:
    """Tests for the init_db helper.

    :author: Ron Webb
    :since: 1.1.0
    """

    def test_creates_db_file(self) -> None:
        """init_db() creates the database file on disk."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            assert os.path.exists(db_path)

    def test_creates_inspections_table(self) -> None:
        """init_db() creates the inspections table."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='inspections'"
            )
            assert cursor.fetchone() is not None
            conn.close()

    def test_idempotent(self) -> None:
        """init_db() can be called multiple times without error."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            init_db(db_path)
            assert os.path.exists(db_path)


class TestInsertResult:
    """Tests for the insert_result helper.

    :author: Ron Webb
    :since: 1.1.0
    """

    def test_record_stored(self) -> None:
        """insert_result() persists a record retrievable via get_results_by_session."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            session_id = str(uuid.uuid4())
            insert_result(db_path, session_id, "/a.py", "CRITICAL", "SQL injection")
            results = get_results_by_session(db_path, session_id)
        assert len(results) == 1
        assert results[0]["file"] == "/a.py"
        assert results[0]["severity"] == "CRITICAL"
        assert results[0]["details"] == "SQL injection"

    def test_multiple_records_stored(self) -> None:
        """insert_result() stores multiple records under the same session."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            session_id = str(uuid.uuid4())
            insert_result(db_path, session_id, "/a.py", "CRITICAL", "x")
            insert_result(db_path, session_id, "/b.py", "MINOR", "y")
            results = get_results_by_session(db_path, session_id)
        assert len(results) == 2


class TestGetResultsBySession:
    """Tests for the get_results_by_session helper.

    :author: Ron Webb
    :since: 1.1.0
    """

    def test_returns_empty_for_unknown_session(self) -> None:
        """get_results_by_session() returns an empty list for an unknown session."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            results = get_results_by_session(db_path, str(uuid.uuid4()))
        assert results == []

    def test_sessions_are_isolated(self) -> None:
        """get_results_by_session() returns only records for the requested session."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            s1 = str(uuid.uuid4())
            s2 = str(uuid.uuid4())
            insert_result(db_path, s1, "/a.py", "CRITICAL", "x")
            insert_result(db_path, s2, "/b.py", "MINOR", "y")
            r1 = get_results_by_session(db_path, s1)
            r2 = get_results_by_session(db_path, s2)
        assert len(r1) == 1 and r1[0]["file"] == "/a.py"
        assert len(r2) == 1 and r2[0]["file"] == "/b.py"

    def test_results_ordered_by_file_path(self) -> None:
        """get_results_by_session() returns records ordered by file_path."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            session_id = str(uuid.uuid4())
            insert_result(db_path, session_id, "/z.py", "NONE", "safe")
            insert_result(db_path, session_id, "/a.py", "MINOR", "x")
            results = get_results_by_session(db_path, session_id)
        assert results[0]["file"] == "/a.py"
        assert results[1]["file"] == "/z.py"


class TestDeleteResultsBySession:
    """Tests for the delete_results_by_session helper.

    :author: Ron Webb
    :since: 1.1.0
    """

    def test_deletes_only_matching_session(self) -> None:
        """delete_results_by_session() removes only records for the given session."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            s1 = str(uuid.uuid4())
            s2 = str(uuid.uuid4())
            insert_result(db_path, s1, "/a.py", "CRITICAL", "x")
            insert_result(db_path, s2, "/b.py", "MINOR", "y")
            delete_results_by_session(db_path, s1)
            assert get_results_by_session(db_path, s1) == []
            assert len(get_results_by_session(db_path, s2)) == 1

    def test_delete_nonexistent_session_is_safe(self) -> None:
        """delete_results_by_session() does not raise for an unknown session."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "vulguard.db")
            init_db(db_path)
            delete_results_by_session(db_path, str(uuid.uuid4()))
