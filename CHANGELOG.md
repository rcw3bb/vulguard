# Changelog

## 1.0.1 - 2026-06-14

### Added

- GitHub Actions **Publish** workflow (`publish.yml`) that runs tests and publishes to PyPI on every push to `main`.
- `_inspect_lock` (`asyncio.Lock`) in `inspector.py` to serialize concurrent Copilot sessions and avoid race conditions.
- `_run_inspection` private helper in `inspector.py` that encapsulates the Copilot client/session lifecycle, keeping the public `inspect_file` API clean.

### Changed

- `_run_inspection` in `cli.py` now wraps inspection and report writing in a `try/finally` block so session data is always cleaned up from the database even when an error occurs.
- `inspect_command` in `cli.py` catches `KeyboardInterrupt` and prints a user-friendly abort message instead of raising an unhandled exception.
- `inspect_file` in `inspector.py` delegates to the new `_run_inspection` helper under the serialization lock.
- `KeyboardInterrupt` inside the Copilot session is converted to `asyncio.CancelledError` for clean async cancellation.

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

