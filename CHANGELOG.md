# Changelog

## 1.1.2 - 2026-06-20

### Fixed

- `_run_inspection()` in `inspector.py` now passes `working_directory` (set to the inspected file's parent directory) to `create_session`, preventing `JsonRpcError -32603` when the process working directory does not exist or is inaccessible.

## 1.1.1 - 2026-06-20

### Added

- `braincraft` package dependency (`>=1.0.0,<2.0.0`) providing `retry_rand_exp` for randomized exponential back-off retry logic.

### Changed

- `_collect_files()` in `cli.py` replaced `path.resolve()` with `path.absolute()` for consistent path resolution without following symlinks.
- `_run_inspection()` in `inspector.py` now uses `braincraft.retry_rand_exp` instead of the internal `retry_async` for transient-failure retry with exponential back-off.

### Removed

- `vulguard/retry.py` — internal retry module superseded by the `braincraft` package.
- `tests/test_retry.py` — unit tests for the removed `retry` module.

## 1.1.0 - 2026-06-14

### Added

- `inspect_command` in `cli.py` exits with code `1` when one or more vulnerabilities are found, enabling CI pipelines to detect and fail on security issues.

## 1.0.3 - 2026-06-14

### Added

- `model` and `extensions` fields added to the report dict in `build_report()` in `report.py`.
- `files_inspected` count field added to the report dict in `build_report()` in `report.py`.
- HTML report header now shows the model name and a second subtitle line displaying the number of files inspected and the targeted extensions.

### Changed

- `_inspect_all()` in `cli.py` replaces the `rich.console.Status` spinner with a `rich.progress.Progress` bar (`BarColumn`, `MofNCompleteColumn`, `TaskProgressColumn`, `TextColumn`, `TimeElapsedColumn`) that advances after each file completes.
- `_inspect_all()` in `cli.py` changed from concurrent `asyncio.gather()` to sequential `await` per file to enable accurate progress tracking.
- `_inspect_and_persist()` in `cli.py` — removed the `status` parameter and spinner-update logic; pylint `too-many-arguments` suppression comment removed.
- `_inspect_all()` in `cli.py` — pylint `too-many-arguments` suppression comment removed.
- `_run_inspection()` in `cli.py` passes `config.get_model()` and `extensions` to `build_report()`.
- `build_report()` in `report.py` accepts new optional `model` and `extensions` parameters.
- `_render_html_report()` in `report.py` handles `%%MODEL%%`, `%%FILES_INSPECTED%%`, and `%%EXTENSIONS%%` substitutions; extensions render as a comma-separated list or `all` when empty.

## 1.0.2 - 2026-06-14

### Added

- `_render_paths_html()` private helper in `report.py` that generates an HTML snippet listing the scanned paths in the report header.

### Changed

- `_inspect_and_persist()` in `cli.py` accepts an optional `status` parameter and updates the Rich spinner message with the currently inspecting file path.
- `_inspect_all()` in `cli.py` passes the live Rich `Status` object to `_inspect_and_persist()` for real-time per-file progress updates.
- `_run_inspection()` in `cli.py` passes the scanned `paths` list to `build_report()` and removes the `try/finally` block — session cleanup now runs unconditionally after reports are written.
- `build_report()` in `report.py` accepts an optional `paths` argument and includes it in the report dict.
- HTML report template updated to render scanned paths in the header via `%%PATHS%%` placeholder.
- Logger configuration in `logging.ini` renamed from `copilotClient` (qualname `copilot.client`) to `copilot` (qualname `copilot`) to align with the Copilot SDK logger hierarchy.

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

