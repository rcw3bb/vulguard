"""
Test fixture: intentionally insecure code demonstrating sensitive payload logging.

This file is for testing purposes only and must NOT be used in production.
"""

import logging

logger = logging.getLogger(__name__)


def process_payment(payload: dict) -> bool:
    """Processes a payment — INSECURE: logs full payload including card data."""
    # SECURITY ISSUE: entire payload (may include card number, CVV, PAN) is logged
    logger.info("Processing payment request: %s", payload)
    # ... payment processing logic ...
    return True


def handle_login(username: str, password: str) -> bool:
    """Handles login — INSECURE: logs credentials."""
    # SECURITY ISSUE: password is logged in plaintext
    logger.debug("Login attempt for user=%s password=%s", username, password)
    return username == "admin"
