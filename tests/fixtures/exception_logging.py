"""
Test fixture: intentionally insecure code demonstrating full exception logging.

This file is for testing purposes only and must NOT be used in production.
"""

import logging
import traceback

logger = logging.getLogger(__name__)


def fetch_user_data(user_id: int) -> dict:
    """Fetches user data — INSECURE: logs entire exception with stack trace."""
    try:
        # Simulated data fetch
        if user_id <= 0:
            raise ValueError(f"Invalid user_id={user_id}")
        return {"id": user_id, "name": "Alice"}
    except Exception as exc:  # noqa: BLE001
        # SECURITY ISSUE: full exception and stack trace logged — may expose
        # sensitive internals, file paths, or data in the exception message
        logger.error("Error fetching user: %s\n%s", exc, traceback.format_exc())
        return {}


def process_request(request: dict) -> dict:
    """Processes a request — INSECURE: logs the whole exception object."""
    try:
        return {"result": request["data"]}
    except Exception as exc:  # noqa: BLE001
        # SECURITY ISSUE: str(exc) may expose sensitive data from the exception
        logger.error("Request processing failed: %s", str(exc))
        return {"error": str(exc)}
