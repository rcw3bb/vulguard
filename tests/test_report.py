"""
tests.test_report - Unit tests for the vulguard.report module.

:author: Ron Webb
:since: 1.0.0
"""

import json
import os
import tempfile

import pytest

from vulguard.report import (
    _HTML_TEMPLATE,
    _render_html_vuln_row,
    build_report,
    write_html,
    write_json,
)


class TestBuildReport:
    """Tests for the build_report function.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_none_severity_filtered_out(self) -> None:
        """build_report() excludes entries with NONE severity."""
        results = [
            {"file": "a.py", "severity": "NONE", "details": "Safe."},
            {"file": "b.py", "severity": "CRITICAL", "details": "SQL injection."},
        ]
        report = build_report(results, "1.0.0")
        vulns = report["vulnerabilities"]
        assert isinstance(vulns, list)
        assert len(vulns) == 1
        assert vulns[0]["severity"] == "CRITICAL"

    def test_report_structure(self) -> None:
        """build_report() returns required top-level keys."""
        report = build_report([], "1.0.0")
        assert report["application"] == "vulguard"
        assert report["version"] == "1.0.0"
        assert report["vulnerabilities"] == []

    def test_multiple_severities_included(self) -> None:
        """build_report() retains CRITICAL, MAJOR, MINOR, and ERROR entries."""
        results = [
            {"file": "a.py", "severity": "CRITICAL", "details": "SQL injection."},
            {"file": "b.py", "severity": "MAJOR", "details": "Weak crypto."},
            {"file": "c.py", "severity": "MINOR", "details": "Logging issue."},
            {"file": "d.py", "severity": "NONE", "details": "Safe."},
            {"file": "e.py", "severity": "ERROR", "details": "Inspection failed."},
        ]
        report = build_report(results, "1.0.0")
        assert len(report["vulnerabilities"]) == 4

    def test_error_severity_included(self) -> None:
        """build_report() retains ERROR severity entries."""
        results = [
            {
                "file": "a.py",
                "severity": "ERROR",
                "details": "Inspection failed: timeout",
            },
        ]
        report = build_report(results, "1.0.0")
        assert len(report["vulnerabilities"]) == 1
        assert report["vulnerabilities"][0]["severity"] == "ERROR"


class TestWriteJson:
    """Tests for the write_json function.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_json_file_written(self) -> None:
        """write_json() produces a valid, loadable JSON file."""
        report: dict[str, object] = {
            "application": "vulguard",
            "version": "1.0.0",
            "vulnerabilities": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "report.json")
            write_json(report, out_path)
            with open(out_path, encoding="utf-8") as rdr:
                loaded = json.load(rdr)
        assert loaded["application"] == "vulguard"

    def test_json_file_indented(self) -> None:
        """write_json() writes indented JSON (not a single line)."""
        report: dict[str, object] = {
            "application": "vulguard",
            "version": "1.0.0",
            "vulnerabilities": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "report.json")
            write_json(report, out_path)
            with open(out_path, encoding="utf-8") as rdr:
                raw = rdr.read()
        assert "\n" in raw


class TestWriteHtml:
    """Tests for the write_html function.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_html_file_written(self) -> None:
        """write_html() creates an HTML file containing severity information."""
        report: dict[str, object] = {
            "application": "vulguard",
            "version": "1.0.0",
            "vulnerabilities": [
                {"file": "a.py", "severity": "CRITICAL", "details": "SQL injection."}
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "report.html")
            write_html(report, out_path)
            with open(out_path, encoding="utf-8") as rdr:
                content = rdr.read()
        assert "<!DOCTYPE html>" in content
        assert "CRITICAL" in content

    def test_error_severity_rendered_in_html(self) -> None:
        """write_html() renders ERROR severity entries with badge and bar styling."""
        report: dict[str, object] = {
            "application": "vulguard",
            "version": "1.0.0",
            "vulnerabilities": [
                {
                    "file": "bad.py",
                    "severity": "ERROR",
                    "details": "Inspection failed: timeout",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "report.html")
            write_html(report, out_path)
            with open(out_path, encoding="utf-8") as rdr:
                content = rdr.read()
        assert 'data-severity="ERROR"' in content
        assert "badge ERROR" in content
        assert "bar ERROR" in content

    def test_no_vulns_shows_safe_message(self) -> None:
        """write_html() shows the no-vulnerability message for an empty report."""
        report: dict[str, object] = {
            "application": "vulguard",
            "version": "1.0.0",
            "vulnerabilities": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "report.html")
            write_html(report, out_path)
            with open(out_path, encoding="utf-8") as rdr:
                content = rdr.read()
        assert "no-vulns" in content

    def test_html_escaping_applied(self) -> None:
        """write_html() escapes HTML-special characters in vulnerability data."""
        report: dict[str, object] = {
            "application": "vulguard",
            "version": "1.0.0",
            "vulnerabilities": [
                {
                    "file": "<script>.py",
                    "severity": "MAJOR",
                    "details": "x&y",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "report.html")
            write_html(report, out_path)
            with open(out_path, encoding="utf-8") as rdr:
                content = rdr.read()
        assert "<script>.py" not in content
        assert "&lt;script&gt;.py" in content


class TestRenderHtmlVulnRow:
    """Tests for the private _render_html_vuln_row helper.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_severity_injected(self) -> None:
        """_render_html_vuln_row() injects the severity value into the row HTML."""
        row = _render_html_vuln_row(
            {"severity": "MAJOR", "file": "x.py", "details": "Issue."}
        )
        assert "MAJOR" in row

    def test_html_escaped(self) -> None:
        """_render_html_vuln_row() escapes HTML special characters in file and details."""
        row = _render_html_vuln_row(
            {"severity": "MINOR", "file": "<script>.py", "details": "x&y."}
        )
        assert "<script>" not in row
        assert "&lt;script&gt;" in row


@pytest.mark.parametrize(
    "severity,expected_css",
    [("CRITICAL", "c-red"), ("MAJOR", "c-orange"), ("MINOR", "c-yellow")],
)
def test_html_template_has_severity_css_classes(
    severity: str, expected_css: str
) -> None:
    """_HTML_TEMPLATE contains the expected CSS class for each severity level."""
    assert expected_css in _HTML_TEMPLATE
