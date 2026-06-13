## Purpose

vulguard is a lightweight CLI security tool (Python >=3.14, Poetry 2.2) that scans source code for vulnerabilities, highlights risky patterns, and guides developers toward safer implementations. The main package is `vulguard`; logging is managed by `logenrich` and configuration bootstrapping by `env-dir-bootstrap`. The runtime config directory is resolved via the `VULGUARD_CONFIG_DIR` environment variable.

Run `poetry install` to set up. Format and lint: `poetry run black vulguard; poetry run pylint vulguard`. Test with coverage: `poetry run pytest --cov=vulguard tests --cov-report html`.

## Tree

- vulguard/ — main package (source code)
- vulguard/__init__.py — package entry point; defines `__version__`, bootstraps config, exposes `CONF_DIR`
- vulguard/logging.ini — logging configuration (bundled as a package resource)
- vulguard/config.ini — default runtime configuration (model name and timeout)
- vulguard/config.py — `Config` class; reads config.ini from CONF_DIR with typed accessors and fallback defaults
- vulguard/cli.py — `main` Click group and `inspect_command`; file collection, orchestration, delegates to `copilot_inspector` and `report`; exposed as the `vulguard` Poetry script
- vulguard/inspector.py — GitHub Copilot SDK integration only; `_load_system_prompt`, `_parse_sdk_response`, `_inspect_file`
- vulguard/db.py — SQLite persistence layer; `get_db_path`, `init_db`, `insert_result`, `get_results_by_session`, `delete_results_by_session`
- vulguard/report.py — JSON and HTML report generation; `build_report`, `write_json`, `write_html`
- vulguard/retry.py — async retry with exponential back-off and full jitter; `_compute_delay`, `retry_async`
- vulguard/prompts/ — bundled prompt resources
- vulguard/prompts/system-prompt.md — security inspection system prompt with JSON response schema
- tests/ — test suite mirroring the vulguard/ package structure
- tests/__init__.py — test package init
- tests/fixtures/ — sample source files used as integration test inputs
- tests/fixtures/sql_injection.py — SQL injection via string formatting
- tests/fixtures/logging_payload.py — sensitive payload/password logging
- tests/fixtures/hardcoded_secret.py — hardcoded API keys and credentials
- tests/fixtures/exception_logging.py — full traceback/exception logging
- tests/fixtures/safe_code.py — clean code with no vulnerabilities
- tests/test_cli.py — unit tests for vulguard.cli
- tests/test_config.py — unit tests for vulguard.config
- tests/test_inspector.py — unit tests for vulguard.inspector (SDK layer only)
- tests/test_db.py — unit tests for vulguard.db
- tests/test_report.py — unit tests for vulguard.report
- tests/test_retry.py — unit tests for vulguard.retry
- .pylintrc — Pylint configuration (must score 10/10)
- pyproject.toml — PEP 621 project metadata and Poetry build config
- CHANGELOG.md — Keep a Changelog format; update for every release
- README.md — project readme with license and version badges
- LICENSE — MIT License

## Rules

- Before adding a new module, place it inside `vulguard/` and mirror its test in `tests/`.
- Before changing `pyproject.toml` dependencies, use `poetry add` or `poetry remove` — never edit the file manually for dependency changes.
- Always keep `README.md` and `vulguard/__init__.py` `__version__` in sync with the version in `pyproject.toml`.
- Always add docstrings (module, class, method), author (`Ron Webb`), and `since` (project version) to every new module and class.
- Use snake_case for methods/variables, PascalCase for classes, UPPER_CASE for constants.
- Use type hints on all method arguments and return types; use `collections.abc` instead of deprecated `typing` aliases.
- Use relative imports within the `vulguard` package.
- Prefix private/protected members with a single underscore `_`.
- Follow SOLID, DRY, and composition-over-inheritance principles; apply dependency injection where applicable.
- Decompose large methods into smaller, focused private helpers.
- Maintain >=80% test coverage; run `poetry run pytest --cov=vulguard tests --cov-report html` to verify.
- Pylint must score 10/10 before committing; fix all warnings.
- Never modify `.pylintrc`, `poetry.lock`, `LICENSE`, or CI config without my approval.
- When you create or discover new files, update the Tree above.

## Note-taking

- After each task, log any correction, preference, or pattern learned.
- Write to the matching docs file's "Session learnings" section; if none fits, add to Rules above. One dated line, plain language. e.g. "Prefer `click.group` over manual argparse for CLI entry points (learned 6/13)"
- 3+ related notes on the same topic → create a new `docs/` context file, move the notes there, and update the Tree. Keep this file under 100 lines.
