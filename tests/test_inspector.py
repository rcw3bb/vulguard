"""
tests.test_inspector - Unit tests for vulguard.inspector (SDK layer).

:author: Ron Webb
:since: 1.0.0
"""

import json

from vulguard.inspector import (
    load_system_prompt,
    _parse_sdk_response,
)


class TestParseSdkResponse:
    """Tests for the _parse_sdk_response helper.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_valid_json_parsed_correctly(self) -> None:
        """_parse_sdk_response() correctly parses a valid JSON response."""
        content = json.dumps(
            {
                "file": "/any.py",
                "severity": "CRITICAL",
                "details": "SQL injection found.",
            }
        )
        result = _parse_sdk_response(content, "/actual.py")
        assert result["file"] == "/actual.py"
        assert result["severity"] == "CRITICAL"
        assert result["details"] == "SQL injection found."

    def test_code_fence_stripped(self) -> None:
        """_parse_sdk_response() strips markdown code fences before parsing."""
        payload = json.dumps({"severity": "MINOR", "details": "Weak crypto."})
        content = f"```json\n{payload}\n```"
        result = _parse_sdk_response(content, "/file.py")
        assert result["severity"] == "MINOR"

    def test_invalid_json_falls_back_to_none(self) -> None:
        """_parse_sdk_response() returns NONE severity on invalid JSON."""
        result = _parse_sdk_response("not-json", "/file.py")
        assert result["severity"] == "NONE"
        assert result["file"] == "/file.py"

    def test_severity_uppercased(self) -> None:
        """_parse_sdk_response() normalises severity to uppercase."""
        content = json.dumps({"severity": "major", "details": "Something."})
        result = _parse_sdk_response(content, "/file.py")
        assert result["severity"] == "MAJOR"

    def test_file_path_overridden(self) -> None:
        """_parse_sdk_response() always uses the provided file_path, not the JSON value."""
        content = json.dumps(
            {"file": "/wrong.py", "severity": "NONE", "details": "Safe."}
        )
        result = _parse_sdk_response(content, "/correct.py")
        assert result["file"] == "/correct.py"


class TestLoadSystemPrompt:
    """Tests for the _load_system_prompt helper.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_returns_non_empty_string(self) -> None:
        """_load_system_prompt() returns a non-empty string."""
        prompt = load_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_contains_json_schema(self) -> None:
        """_load_system_prompt() includes the expected JSON schema keywords."""
        prompt = load_system_prompt()
        assert "severity" in prompt
        assert "CRITICAL" in prompt
