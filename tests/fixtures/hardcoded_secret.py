"""
Test fixture: intentionally insecure code demonstrating hardcoded secrets.

This file is for testing purposes only and must NOT be used in production.
"""

# SECURITY ISSUE: hardcoded API key embedded in source code
API_KEY = "sk-abc123xyz987-hardcoded-secret-key"

# SECURITY ISSUE: hardcoded database password
DB_PASSWORD = "SuperSecret@Password123!"

# SECURITY ISSUE: hardcoded JWT secret
JWT_SECRET = "my-jwt-signing-secret-do-not-share"


def get_api_client():
    """Creates an API client using the hardcoded key — INSECURE."""
    return {"key": API_KEY, "url": "https://api.example.com"}


def connect_database():
    """Returns a DB connection string with embedded password — INSECURE."""
    return f"postgresql://admin:{DB_PASSWORD}@localhost:5432/appdb"
