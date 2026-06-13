"""
Test fixture: safe code with no security vulnerabilities.

This file is for testing purposes only.
"""

import hashlib
import secrets


def hash_password(password: str) -> str:
    """Hashes a password securely using SHA-256 with a salt.

    :param password: The plaintext password to hash.
    :return: A hex digest string.
    """
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{digest}"


def generate_token(length: int = 32) -> str:
    """Generates a cryptographically secure random token.

    :param length: The number of bytes of randomness.
    :return: A URL-safe token string.
    """
    return secrets.token_urlsafe(length)


def add_numbers(a: int, b: int) -> int:
    """Returns the sum of two integers.

    :param a: First operand.
    :param b: Second operand.
    :return: The sum.
    """
    return a + b
