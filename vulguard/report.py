"""
vulguard.report - JSON and HTML report generation for vulguard security scan results.

Provides functions to build the report data structure from raw inspection results
and to serialise it to JSON and self-contained HTML output files.

:author: Ron Webb
:since: 1.0.0
"""

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

_APPLICATION_NAME = "vulguard"

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vulguard Security Report</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f4f6f8; color: #333; padding: 32px; }
        h1 { font-size: 24px; margin-bottom: 4px; }
        .header { background: #1a1a2e; color: #fff; padding: 28px 32px;
                  border-radius: 10px; margin-bottom: 24px; }
        .header .sub { font-size: 13px; opacity: 0.65; margin-top: 6px; }
        .summary { display: flex; gap: 16px; margin-bottom: 28px; }
        .card { background: #fff; border-radius: 10px; padding: 20px; flex: 1;
                text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
        .card .num { font-size: 34px; font-weight: 700; }
        .card .lbl { font-size: 12px; color: #777; margin-top: 4px;
                     text-transform: uppercase; letter-spacing: .5px; }
        .card { cursor: pointer; transition: box-shadow .15s, transform .1s; }
        .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.13); transform: translateY(-2px); }
        .card.active { outline: 2px solid #1a1a2e; }
        .c-red { color: #c0392b; } .c-orange { color: #e67e22; } .c-yellow { color: #d4ac0d; } .c-grey { color: #7f8c8d; }
        .paths { font-size: 12px; opacity: 0.75; margin-top: 6px; font-family: monospace; }
        .paths code { background: rgba(255,255,255,0.15); padding: 1px 6px; border-radius: 4px; }
        .vuln { background: #fff; border-radius: 10px; margin-bottom: 16px;
                overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08); display: flex; }
        .bar { width: 6px; flex-shrink: 0; }
        .bar.CRITICAL { background: #c0392b; }
        .bar.MAJOR    { background: #e67e22; }
        .bar.MINOR    { background: #d4ac0d; }
        .bar.ERROR    { background: #7f8c8d; }
        .body { padding: 18px 20px; flex: 1; }
        .badge { display: inline-block; padding: 2px 10px; border-radius: 12px;
                 font-size: 11px; font-weight: 700; text-transform: uppercase; margin-right: 10px; }
        .badge.CRITICAL { background: #fdecea; color: #c0392b; }
        .badge.MAJOR    { background: #fef0e6; color: #e67e22; }
        .badge.MINOR    { background: #fef9e7; color: #d4ac0d; }
        .badge.ERROR    { background: #eaecee; color: #7f8c8d; }
        .file { font-size: 12px; font-family: monospace; color: #555; }
        .details { margin-top: 8px; font-size: 14px; color: #555; line-height: 1.55; }
        .no-vulns { text-align: center; padding: 48px; color: #888; font-size: 16px;
                    background: #fff; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
    </style>
</head>
<body>
    <div class="header">
        <h1>Vulguard Security Report</h1>
        <div class="sub">%%APPLICATION%% &bull; v%%VERSION%% &bull; %%MODEL%% &bull; %%TIMESTAMP%%</div>
        <div class="sub">%%FILES_INSPECTED%% file(s) inspected &bull; Extensions: %%EXTENSIONS%%</div>
        %%PATHS%%
    </div>
    <div class="summary">
        <div class="card active" data-filter="ALL" onclick="filterCards(this)"><div class="num">%%TOTAL%%</div><div class="lbl">Vulnerabilities</div></div>
        <div class="card" data-filter="CRITICAL" onclick="filterCards(this)"><div class="num c-red">%%CRITICAL%%</div><div class="lbl">Critical</div></div>
        <div class="card" data-filter="MAJOR" onclick="filterCards(this)"><div class="num c-orange">%%MAJOR%%</div><div class="lbl">Major</div></div>
        <div class="card" data-filter="MINOR" onclick="filterCards(this)"><div class="num c-yellow">%%MINOR%%</div><div class="lbl">Minor</div></div>
        <div class="card" data-filter="ERROR" onclick="filterCards(this)"><div class="num c-grey">%%ERROR%%</div><div class="lbl">Error</div></div>
    </div>
    %%ROWS%%%%NO_VULNS%%
    <script>
        function filterCards(el) {
            document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            var filter = el.getAttribute('data-filter');
            document.querySelectorAll('.vuln').forEach(function(row) {
                row.style.display = (filter === 'ALL' || row.getAttribute('data-severity') === filter) ? 'flex' : 'none';
            });
        }
    </script>
</body>
</html>
"""

_HTML_ROW_TEMPLATE = (
    '<div class="vuln" data-severity="%%SEVERITY%%">'
    '<div class="bar %%SEVERITY%%"></div>'
    '<div class="body">'
    '<span class="badge %%SEVERITY%%">%%SEVERITY%%</span>'
    '<span class="file">%%FILE%%</span>'
    '<div class="details">%%DETAILS%%</div>'
    "</div>"
    "</div>\n"
)


def build_report(
    results: list[dict[str, str]],
    version: str,
    paths: list[str] | None = None,
    model: str | None = None,
    extensions: list[str] | None = None,
) -> dict[str, object]:
    """Builds the final report dict, filtering out ``NONE``-severity entries.

    :param results: List of per-file inspection result dicts.
    :param version: The application version string.
    :param paths: Optional list of scanned paths provided to the CLI.
    :param model: Optional model identifier used during inspection.
    :param extensions: Optional list of file extensions targeted during inspection.
    :return: Structured report dict ready for JSON serialisation.
    """
    vulnerabilities: list[dict[str, str]] = [
        r for r in results if r.get("severity") != "NONE"
    ]
    return {
        "application": _APPLICATION_NAME,
        "version": version,
        "model": model or "",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files_inspected": len(results),
        "extensions": extensions if extensions is not None else [],
        "paths": paths if paths is not None else [],
        "vulnerabilities": vulnerabilities,
    }


def _render_paths_html(paths: list[str]) -> str:
    """Renders the scanned-paths line for the HTML report header.

    :param paths: List of scanned paths supplied to the CLI.
    :return: HTML string for the paths section, or empty string if no paths.
    """
    if not paths:
        return ""
    items = " &bull; ".join(f"<code>{html.escape(p)}</code>" for p in paths)
    return f'<div class="paths">Scanned: {items}</div>'


def _render_html_vuln_row(vuln: dict[str, str]) -> str:
    """Renders a single vulnerability as an HTML card row.

    :param vuln: Vulnerability dict with ``file``, ``severity``, and ``details``.
    :return: HTML string for the vulnerability card.
    """
    substitutions = {
        "SEVERITY": str(vuln.get("severity", "MINOR")),
        "FILE": html.escape(str(vuln.get("file", ""))),
        "DETAILS": html.escape(str(vuln.get("details", ""))),
    }
    return re.sub(
        r"%%(\w+)%%",
        lambda m: substitutions.get(m.group(1), m.group(0)),
        _HTML_ROW_TEMPLATE,
    )


def _render_html_report(report: dict[str, object], vulns: list[dict[str, str]]) -> str:
    """Renders the complete HTML report as a string.

    :param report: The full report dict.
    :param vulns: The list of vulnerability dicts to render.
    :return: Rendered HTML string.
    """
    rows = "".join(_render_html_vuln_row(v) for v in vulns)
    no_vulns = (
        ""
        if vulns
        else '<p class="no-vulns">No vulnerabilities found. Your code looks safe!</p>'
    )
    raw_paths = report.get("paths", [])
    paths: list[str] = raw_paths if isinstance(raw_paths, list) else []
    raw_extensions = report.get("extensions", [])
    extensions: list[str] = raw_extensions if isinstance(raw_extensions, list) else []
    extensions_label = ", ".join(extensions) if extensions else "all"
    substitutions = {
        "APPLICATION": html.escape(str(report.get("application", _APPLICATION_NAME))),
        "VERSION": html.escape(str(report.get("version", ""))),
        "MODEL": html.escape(str(report.get("model", ""))),
        "TIMESTAMP": html.escape(str(report.get("timestamp", ""))),
        "FILES_INSPECTED": str(report.get("files_inspected", 0)),
        "EXTENSIONS": html.escape(extensions_label),
        "PATHS": _render_paths_html(paths),
        "TOTAL": str(len(vulns)),
        "CRITICAL": str(sum(1 for v in vulns if v.get("severity") == "CRITICAL")),
        "MAJOR": str(sum(1 for v in vulns if v.get("severity") == "MAJOR")),
        "MINOR": str(sum(1 for v in vulns if v.get("severity") == "MINOR")),
        "ERROR": str(sum(1 for v in vulns if v.get("severity") == "ERROR")),
        "ROWS": rows,
        "NO_VULNS": no_vulns,
    }
    return re.sub(
        r"%%(\w+)%%",
        lambda m: substitutions.get(m.group(1), m.group(0)),
        _HTML_TEMPLATE,
    )


def write_json(report: dict[str, object], path: Path) -> None:
    """Writes the report as a JSON file.

    :param report: The report dict to serialise.
    :param path: Destination file path.
    """
    with open(path, "w", encoding="utf-8") as file_out:
        json.dump(report, file_out, indent=2)


def write_html(report: dict[str, object], path: Path) -> None:
    """Writes the report as a self-contained HTML file.

    :param report: The report dict containing the ``vulnerabilities`` list.
    :param path: Destination file path.
    """
    raw_vulns = report.get("vulnerabilities", [])
    vulns: list[dict[str, str]] = []
    if isinstance(raw_vulns, list):
        vulns = [v for v in raw_vulns if isinstance(v, dict)]
    html_content = _render_html_report(report, vulns)
    with open(path, "w", encoding="utf-8") as file_out:
        file_out.write(html_content)
