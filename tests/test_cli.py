"""
tests.test_cli - Unit tests for the vulguard.cli module.

:author: Ron Webb
:since: 1.0.0
"""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from vulguard.cli import (
    _collect_files,
    _run_inspection,
    _should_include,
    inspect_command,
    main,
)


class TestShouldInclude:
    """Tests for the _should_include helper.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_empty_extensions_includes_all(self) -> None:
        """_should_include() returns True for any file when extensions is empty."""
        assert _should_include("file.txt", []) is True

    def test_matching_extension_included(self) -> None:
        """_should_include() returns True when the extension matches."""
        assert _should_include("script.py", ["py"]) is True

    def test_non_matching_extension_excluded(self) -> None:
        """_should_include() returns False when the extension does not match."""
        assert _should_include("archive.zip", ["py", "js"]) is False

    def test_case_insensitive_match(self) -> None:
        """_should_include() matches extensions case-insensitively."""
        assert _should_include("MODULE.PY", ["py"]) is True


class TestCollectFiles:
    """Tests for the _collect_files helper.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_direct_file_included(self) -> None:
        """_collect_files() includes a directly specified file."""
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "app.py")
            with open(target, "w", encoding="utf-8") as out:
                out.write("x = 1\n")
            result = _collect_files((target,), [])
            assert os.path.abspath(target) in result

    def test_recursive_directory_walk(self) -> None:
        """_collect_files() recursively collects files from a directory."""
        with tempfile.TemporaryDirectory() as tmp:
            sub = os.path.join(tmp, "sub")
            os.makedirs(sub)
            for name in ("a.py", "b.py", os.path.join("sub", "c.py")):
                path = os.path.join(tmp, name)
                with open(path, "w", encoding="utf-8") as out:
                    out.write("x = 1\n")
            result = _collect_files((tmp,), [])
            assert len(result) == 3

    def test_extension_filter_applied(self) -> None:
        """_collect_files() filters files by extension."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("script.py", "style.css", "readme.md"):
                path = os.path.join(tmp, name)
                with open(path, "w", encoding="utf-8") as out:
                    out.write("content\n")
            result = _collect_files((tmp,), ["py"])
            assert all(f.endswith(".py") for f in result)
            assert len(result) == 1

    def test_result_is_sorted(self) -> None:
        """_collect_files() returns files in sorted order."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("z.py", "a.py", "m.py"):
                path = os.path.join(tmp, name)
                with open(path, "w", encoding="utf-8") as out:
                    out.write("x = 1\n")
            result = _collect_files((tmp,), [])
            assert result == sorted(result)


class TestRunInspection:
    """Tests for the async _run_inspection orchestrator.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_run_inspection_creates_json_report(self) -> None:
        """_run_inspection() creates a JSON report file when files are found."""
        mock_result = {
            "file": "/some/file.py",
            "severity": "CRITICAL",
            "details": "SQL injection.",
        }
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "app.py")
            with open(target, "w", encoding="utf-8") as out:
                out.write("x = 1\n")
            with patch(
                "vulguard.cli.inspect_file",
                new=AsyncMock(return_value=mock_result),
            ):
                asyncio.run(
                    _run_inspection((tmp,), [], tmp, "test-report", "json", tmp)
                )
            json_files = [f for f in os.listdir(tmp) if f.endswith(".json")]
            assert len(json_files) == 1
            report_path = os.path.join(tmp, json_files[0])
            with open(report_path, encoding="utf-8") as rdr:
                report = json.load(rdr)
        assert report["application"] == "vulguard"
        assert len(report["vulnerabilities"]) == 1
        assert "paths" in report
        assert isinstance(report["paths"], list)

    def test_run_inspection_creates_html_report(self) -> None:
        """_run_inspection() creates both JSON and HTML reports when fmt='html'."""
        mock_result = {
            "file": "/some/file.py",
            "severity": "MINOR",
            "details": "Weak crypto.",
        }
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "module.py")
            with open(target, "w", encoding="utf-8") as out:
                out.write("x = 1\n")
            with patch(
                "vulguard.cli.inspect_file",
                new=AsyncMock(return_value=mock_result),
            ):
                asyncio.run(
                    _run_inspection((tmp,), [], tmp, "test-report", "html", tmp)
                )
            html_files = [f for f in os.listdir(tmp) if f.endswith(".html")]
            json_files = [f for f in os.listdir(tmp) if f.endswith(".json")]
        assert len(html_files) == 1
        assert len(json_files) == 1

    def test_run_inspection_no_files(self) -> None:
        """_run_inspection() exits early when no files match the filter."""
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = os.path.join(tmp, "reports")
            asyncio.run(
                _run_inspection((tmp,), ["xyz"], out_dir, "test-report", "json", tmp)
            )
            assert not os.path.exists(out_dir)

    def test_run_inspection_handles_inspect_error(self) -> None:
        """_run_inspection() continues past a file that raises an exception."""
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "bad.py")
            with open(target, "w", encoding="utf-8") as out:
                out.write("x = 1\n")
            with patch(
                "vulguard.cli.inspect_file",
                new=AsyncMock(side_effect=RuntimeError("SDK error")),
            ):
                asyncio.run(
                    _run_inspection((tmp,), [], tmp, "test-report", "json", tmp)
                )
            json_files = [f for f in os.listdir(tmp) if f.endswith(".json")]
        assert len(json_files) == 1


class TestCliInspectCommand:
    """Tests for the inspect_command Click entry point.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_cli_help(self) -> None:
        """inspect_command --help exits 0 and shows usage text."""
        runner = CliRunner()
        result = runner.invoke(inspect_command, ["--help"])
        assert result.exit_code == 0
        assert "PATHS" in result.output

    def test_cli_missing_paths_exits_nonzero(self) -> None:
        """inspect_command exits with a non-zero code when no PATHS are given."""
        runner = CliRunner()
        result = runner.invoke(inspect_command, [])
        assert result.exit_code != 0

    def test_cli_runs_with_valid_path(self) -> None:
        """inspect_command invokes _run_inspection for a valid directory."""
        mock_async = AsyncMock(return_value=None)
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vulguard.cli._run_inspection", mock_async):
                result = runner.invoke(inspect_command, [tmp])
        assert result.exit_code == 0
        mock_async.assert_awaited_once()

    def test_cli_ext_parsed_correctly(self) -> None:
        """inspect_command passes parsed extension list to _run_inspection."""
        captured: list = []

        async def fake_run(paths, extensions, output_dir, report_base, fmt, db_dir):
            """Captures arguments for assertion."""
            captured.append(extensions)

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vulguard.cli._run_inspection", fake_run):
                runner.invoke(inspect_command, [tmp, "--ext", "py,js"])
        assert captured and captured[0] == ["py", "js"]

    def test_cli_default_format_is_json(self) -> None:
        """inspect_command defaults to json format."""
        captured: list = []

        async def fake_run(paths, extensions, output_dir, report_base, fmt, db_dir):
            """Captures fmt argument for assertion."""
            captured.append(fmt)

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vulguard.cli._run_inspection", fake_run):
                runner.invoke(inspect_command, [tmp])
        assert captured and captured[0] == "json"

    def test_cli_custom_report_name(self) -> None:
        """inspect_command passes the custom report base name to _run_inspection."""
        captured: list = []

        async def fake_run(paths, extensions, output_dir, report_base, fmt, db_dir):
            """Captures report_base for assertion."""
            captured.append(report_base)

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vulguard.cli._run_inspection", fake_run):
                runner.invoke(inspect_command, [tmp, "--report", "my-scan"])
        assert captured and captured[0] == "my-scan"


class TestMainGroup:
    """Tests for the main Click group entry point.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_main_help(self) -> None:
        """main --help exits 0 and shows the group description."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0

    def test_main_has_inspect_subcommand(self) -> None:
        """main group exposes the inspect sub-command."""
        runner = CliRunner()
        result = runner.invoke(main, ["inspect", "--help"])
        assert result.exit_code == 0
        assert "PATHS" in result.output

    def test_version_flag(self) -> None:
        """--version prints the application name and version then exits 0."""
        from vulguard import __version__  # pylint: disable=import-outside-toplevel

        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "vulguard" in result.output
        assert __version__ in result.output

    def test_version_short_flag(self) -> None:
        """-V is an alias for --version."""
        from vulguard import __version__  # pylint: disable=import-outside-toplevel

        runner = CliRunner()
        result = runner.invoke(main, ["-V"])
        assert result.exit_code == 0
        assert __version__ in result.output
