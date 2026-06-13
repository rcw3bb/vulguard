# Changelog

## 1.0.0 - 2026-06-14

### Added

- Initial release of vulguard.
- Lightweight security scanning for source code vulnerabilities.
- Highlights risky patterns and guides developers toward safer implementations.
- GitHub Actions **Tests** workflow for automated formatting check, linting, and test runs (with 80% coverage gate) on every push and pull request.
- Async retry mechanism with exponential back-off and full jitter (`vulguard/retry.py`).
- `--version` / `-V` CLI flag to display the installed package version.
- Concurrent file inspection using `asyncio.gather()` for improved throughput.
- `_inspect_and_persist()` helper decomposing per-file inspection and database persistence.
- `_inspect_all()` helper orchestrating concurrent per-file inspection tasks.
- `_run_inspection()` helper orchestrating file collection, inspection, and report writing.
- `_setup_db_session()` helper encapsulating database initialisation and session creation.
- `_write_reports()` helper encapsulating JSON and HTML report writing.
- Additional configuration keys in `config.ini` for model name, timeout, and retry back-off settings (`max-attempts`, `base-delay`, `max-delay`).
- Typed accessors in the `Config` class for model, timeout, and retry back-off configuration (`get_model`, `get_timeout`, `get_max_attempts`, `get_base_delay`, `get_max_delay`).
- Expanded test suite covering `retry.py` and additional cases for `cli.py` and `inspector.py`.

