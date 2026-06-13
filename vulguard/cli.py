"""
vulguard.cli - Command-line interface for the vulguard security inspection tool.

Defines the Click command group and the ``inspect`` sub-command. Handles
recursive file collection, orchestrates per-file Copilot inspections (results
persisted to SQLite via ``vulguard.db``), and delegates report generation to
``vulguard.report``.

:author: Ron Webb
:since: 1.0.0
"""

import asyncio
import uuid
from pathlib import Path

import click
from logenrich import setup_logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import __version__, CONF_DIR
from .config import Config
from .db import (
    delete_results_by_session,
    get_db_path,
    get_results_by_session,
    init_db,
    insert_result,
)
from .inspector import inspect_file, load_system_prompt
from .report import build_report, write_html, write_json

_console = Console()
_logger = setup_logger(__name__, conf_dir=CONF_DIR)


def _should_include(path: str | Path, extensions: list[str]) -> bool:
    """Determines whether a file should be included based on its extension.

    :param path: The file path to evaluate.
    :param extensions: List of allowed extensions without dots. Empty means all files.
    :return: True if the file should be included.
    """
    if not extensions:
        return True
    return Path(path).suffix.lstrip(".").lower() in extensions


def _collect_files(paths: tuple[str, ...], extensions: list[str]) -> list[str]:
    """Collects files from the given paths, recursively walking directories.

    :param paths: Tuple of file or directory paths supplied by the user.
    :param extensions: List of allowed extensions. Empty list means all files.
    :return: Sorted list of unique absolute file paths.
    """
    collected: set[str] = set()
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file():
            if _should_include(path, extensions):
                collected.add(str(path.resolve()))
        elif path.is_dir():
            for file_path in path.rglob("*"):
                if file_path.is_file() and _should_include(file_path, extensions):
                    collected.add(str(file_path.resolve()))
    return sorted(collected)


async def _inspect_and_persist(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    file_path: str,
    system_prompt: str,
    config: Config,
    db_path: str,
    session_id: str,
    status: object | None = None,
) -> None:
    """Inspects a single file and persists the result to the database.

    :param file_path: Absolute path to the file to inspect.
    :param system_prompt: The security inspection system prompt text.
    :param config: The vulguard configuration instance.
    :param db_path: Absolute path to the vulguard SQLite database file.
    :param session_id: UUID string identifying the current inspection run.
    :param status: Optional Rich Status object used to update the spinner message.
    """
    _logger.debug("Inspecting file: %s", file_path)
    if status is not None:
        status.update(f"Inspecting: {file_path}")
    severity = "NONE"
    details = "The code is safe."
    try:
        result = await inspect_file(file_path, system_prompt, config)
        severity = result.get("severity", "NONE")
        details = result.get("details", "The code is safe.")
        _logger.debug(
            "Inspection complete for %s — severity: %s",
            file_path,
            severity,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        severity = "ERROR"
        details = f"Inspection failed: {exc}"
        _logger.error("Failed to inspect %s: %s", file_path, exc)
        _console.print(f"[red]Failed to inspect {file_path}: {exc}[/red]")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None, insert_result, db_path, session_id, file_path, severity, details
    )


async def _inspect_all(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    files: list[str],
    system_prompt: str,
    config: Config,
    db_path: str,
    session_id: str,
) -> None:
    """Runs inspection for each file concurrently and persists each result to the database.

    :param files: Sorted list of absolute file paths to inspect.
    :param system_prompt: The security inspection system prompt text.
    :param config: The vulguard configuration instance.
    :param db_path: Absolute path to the vulguard SQLite database file.
    :param session_id: UUID string identifying the current inspection run.
    """
    with _console.status("Inspecting…", spinner="dots") as status:
        tasks = [
            _inspect_and_persist(fp, system_prompt, config, db_path, session_id, status)
            for fp in files
        ]
        await asyncio.gather(*tasks)


def _setup_db_session(db_dir: str | None) -> tuple[str, str]:
    """Initialises the SQLite database and creates a new inspection session.

    :param db_dir: Optional directory override for the database location.
    :return: Tuple of ``(db_path, session_id)``.
    """
    db_path = get_db_path(db_dir)
    init_db(db_path)
    session_id = str(uuid.uuid4())
    _logger.debug("Inspection session: %s  db: %s", session_id, db_path)
    return db_path, session_id


def _write_reports(
    report: dict[str, object],
    output_dir: str,
    report_base: str,
    fmt: str,
) -> None:
    """Writes the JSON report and, optionally, the HTML report to disk.

    :param report: The report dict produced by :func:`.report.build_report`.
    :param output_dir: Directory where report files are written.
    :param report_base: Base filename (no extension).
    :param fmt: ``'json'`` or ``'html'``; ``'html'`` also produces a JSON file.
    """
    output_path = Path(output_dir)
    json_path = output_path / f"{report_base}.json"
    write_json(report, json_path)
    _logger.info("JSON report written: %s", json_path)
    _console.print(f"[green]JSON report:[/green] {json_path}")

    if fmt == "html":
        html_path = output_path / f"{report_base}.html"
        write_html(report, html_path)
        _logger.info("HTML report written: %s", html_path)
        _console.print(f"[green]HTML report:[/green] {html_path}")


async def _run_inspection(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    paths: tuple[str, ...],
    extensions: list[str],
    output_dir: str,
    report_base: str,
    fmt: str,
    db_dir: str | None = None,
) -> None:
    """Orchestrates file collection, Copilot inspection, and report writing.

    Inspection results are persisted to SQLite (``vulguard.db``) during the
    run.  After the report is written the session records are deleted.

    :param paths: Tuple of file or directory paths to inspect.
    :param extensions: File extension filter list (empty = all files).
    :param output_dir: Directory where reports are written.
    :param report_base: Base filename for the report (no suffix appended).
    :param fmt: Report format — ``'json'`` or ``'html'``.
    :param db_dir: Optional directory that overrides the default database
                   location (``~/.vulguard``).
    """
    _logger.info("Starting vulguard inspection — paths: %s, fmt: %s", paths, fmt)
    system_prompt = load_system_prompt()
    config = Config()
    files = _collect_files(paths, extensions)

    if not files:
        _logger.warning("No files found matching the specified criteria.")
        _console.print(
            "[yellow]No files found matching the specified criteria.[/yellow]"
        )
        return

    db_path, session_id = _setup_db_session(db_dir)
    _logger.info("Collected %d file(s) for inspection.", len(files))
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    await _inspect_all(files, system_prompt, config, db_path, session_id)

    results = get_results_by_session(db_path, session_id)
    report = build_report(results, __version__, list(paths))
    vuln_count = sum(1 for r in results if r.get("severity") != "NONE")

    _write_reports(report, output_dir, report_base, fmt)

    delete_results_by_session(db_path, session_id)
    _logger.debug("Session %s removed from database.", session_id)

    _logger.info("Inspection complete. %d vulnerability(ies) found.", vuln_count)
    _console.print(
        f"\n[bold]Inspection complete.[/bold] {vuln_count} vulnerability(ies) found."
    )


@click.command("inspect")
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--ext",
    default=None,
    help=(
        "Comma-separated file extensions to inspect (e.g. py,js,ts). "
        "Inspects all files if omitted."
    ),
)
@click.option(
    "--output-dir",
    default=None,
    type=click.Path(),
    help="Output directory for reports. Defaults to <cwd>/reports.",
)
@click.option(
    "--report",
    default="vulguard-report",
    show_default=True,
    help="Base filename for the report (no suffix appended).",
)
@click.option(
    "--format",
    "fmt",
    default="json",
    show_default=True,
    type=click.Choice(["json", "html"]),
    help="Report format. Choosing 'html' also produces a JSON file.",
)
@click.option(
    "--db-dir",
    default=None,
    type=click.Path(),
    help="Directory for the vulguard SQLite database. Defaults to ~/.vulguard.",
)
def inspect_command(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    paths: tuple[str, ...],
    ext: str | None,
    output_dir: str | None,
    report: str,
    fmt: str,
    db_dir: str | None,
) -> None:
    """Inspect source files or directories for security vulnerabilities.

    PATHS are one or more file or directory paths to inspect.
    Directories are walked recursively. Each file is inspected in an
    isolated GitHub Copilot session.
    """
    extensions: list[str] = [e.strip().lower() for e in ext.split(",")] if ext else []
    effective_output_dir = output_dir or str(Path.cwd() / "reports")
    try:
        asyncio.run(
            _run_inspection(
                paths, extensions, effective_output_dir, report, fmt, db_dir
            )
        )
    except KeyboardInterrupt:
        _console.print("\n[yellow]Inspection aborted.[/yellow]")


@click.group()
@click.version_option(
    __version__, "--version", "-V", prog_name="vulguard", message="%(prog)s %(version)s"
)
def main() -> None:
    """vulguard - AI-powered source code security inspector."""
    banner = Text.assemble(
        ("vulguard", "bold cyan"),
        (" v", "dim"),
        (__version__, "bold white"),
        " - ",
        ("AI-powered source code security inspector", "dim"),
    )
    _console.print(Panel(banner, expand=False, border_style="cyan"))


main.add_command(inspect_command)
