"""
vulguard.inspector - GitHub Copilot SDK integration for security file inspection.

Loads the system prompt, sends each file to an isolated Copilot session,
and parses the model response into a structured vulnerability dict.

:author: Ron Webb
:since: 1.0.0
"""

import json
from importlib import resources
from pathlib import Path

from copilot import CopilotClient  # pylint: disable=import-error
from copilot.session import PermissionHandler  # pylint: disable=import-error
from copilot.session_events import AssistantMessageData  # pylint: disable=import-error

from .config import Config
from .retry import retry_async


def load_system_prompt() -> str:
    """Loads the security inspection system prompt from the package resources.

    :return: The full system prompt text.
    """
    prompt_ref = resources.files("vulguard").joinpath("prompts/system-prompt.md")
    return prompt_ref.read_text(encoding="utf-8")


def _parse_sdk_response(content: str, file_path: str) -> dict[str, str]:
    """Parses the JSON response returned by the Copilot model.

    Strips markdown code fences if present and falls back to a safe ``NONE``
    entry on any parse failure.

    :param content: Raw text response from the model.
    :param file_path: The inspected file path used as the ``file`` field value.
    :return: Dict with ``file``, ``severity``, and ``details`` keys.
    """
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1]).strip()
    try:
        data = json.loads(cleaned)
        return {
            "file": file_path,
            "severity": str(data.get("severity", "NONE")).upper(),
            "details": str(data.get("details", "The code is safe.")),
        }
    except json.JSONDecodeError, ValueError:
        return {
            "file": file_path,
            "severity": "NONE",
            "details": "The code is safe.",
        }


async def inspect_file(
    file_path: str,
    system_prompt: str,
    config: Config,
) -> dict[str, str]:
    """Inspects a single file using an isolated GitHub Copilot session.

    A new ``CopilotClient`` and session are created for each file to ensure
    full context isolation between inspections.  The ``send_and_wait`` call is
    wrapped with :func:`.retry.retry_async` to transparently retry transient
    failures using exponential back-off with full jitter.

    :param file_path: Absolute path to the file to inspect.
    :param system_prompt: The security inspection system prompt text.
    :param config: The vulguard configuration instance.
    :return: Dict with ``file``, ``severity``, and ``details`` keys.
    """
    async with CopilotClient() as client:
        async with await client.create_session(
            on_permission_request=PermissionHandler.approve_all,
            model=config.get_model(),
            system_message={"mode": "replace", "content": system_prompt},
        ) as session:
            response = await retry_async(
                session.send_and_wait,
                f"Check for security vulnerability the {file_path}",
                attachments=[
                    {
                        "type": "file",
                        "path": file_path,
                        "displayName": Path(file_path).name,
                    }
                ],
                timeout=float(config.get_timeout()),
                max_attempts=config.get_max_attempts(),
                base_delay=config.get_base_delay(),
                max_delay=config.get_max_delay(),
            )

    if response is None:
        return {"file": file_path, "severity": "NONE", "details": "The code is safe."}

    content = ""
    if isinstance(response.data, AssistantMessageData):
        content = response.data.content or ""

    return _parse_sdk_response(content, file_path)
