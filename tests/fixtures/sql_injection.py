"""
Test fixture: intentionally insecure code demonstrating SQL injection.

This file is for testing purposes only and must NOT be used in production.
"""

import sqlite3


def get_user(username: str) -> dict:
    """Returns user record — INSECURE: vulnerable to SQL injection."""
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # SECURITY ISSUE: SQL built with string formatting — SQL injection risk
    query = "SELECT * FROM users WHERE username = '%s'" % username
    cursor.execute(query)
    row = cursor.fetchone()
    conn.close()
    return {"user": row}


def delete_record(record_id: str) -> None:
    """Deletes a record — INSECURE: vulnerable to SQL injection."""
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    # SECURITY ISSUE: f-string SQL construction without parameterization
    cursor.execute(f"DELETE FROM records WHERE id = {record_id}")
    conn.commit()
    conn.close()
