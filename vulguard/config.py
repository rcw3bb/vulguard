"""
vulguard.config - Configuration management module for vulguard.

Reads settings from the bootstrapped config.ini file and provides
typed accessors with sensible defaults.

:author: Ron Webb
:since: 1.0.0
"""

import configparser
from pathlib import Path

from . import CONF_DIR

_DEFAULT_MODEL = "claude-sonnet-4.6"
_DEFAULT_TIMEOUT = 300
_DEFAULT_MAX_ATTEMPTS = 5
_DEFAULT_BASE_DELAY = 0.5
_DEFAULT_MAX_DELAY = 10.0


class Config:
    """
    Manages the vulguard configuration from config.ini.

    Reads from the bootstrapped configuration directory (``CONF_DIR``) and
    provides typed accessors for configuration values with sensible defaults
    so that the application continues to function even when the file is absent.

    :author: Ron Webb
    :since: 1.0.0
    """

    def __init__(self, conf_dir: str | None = None) -> None:
        """Initialises the configuration by reading config.ini from CONF_DIR.

        :param conf_dir: Optional directory override for the config file location.
                         Falls back to the bootstrapped ``CONF_DIR`` when omitted.
        """
        self._config = configparser.ConfigParser()
        config_path = Path(conf_dir or CONF_DIR) / "config.ini"
        self._config.read(config_path)

    def get_model(self) -> str:
        """Returns the configured Copilot model name.

        Falls back to ``claude-sonnet-4.6`` if the key is absent.

        :return: The model identifier string.
        """
        return self._config.get("model", "model", fallback=_DEFAULT_MODEL)

    def get_timeout(self) -> int:
        """Returns the configured inspection timeout in seconds.

        Falls back to 300 seconds if the key is absent.

        :return: Timeout as a positive integer number of seconds.
        """
        return self._config.getint("model", "timeout", fallback=_DEFAULT_TIMEOUT)

    def get_max_attempts(self) -> int:
        """Returns the maximum number of retry attempts.

        Falls back to 5 if the key is absent.

        :return: Maximum retry attempt count as a positive integer.
        """
        return self._config.getint(
            "retry", "max-attempts", fallback=_DEFAULT_MAX_ATTEMPTS
        )

    def get_base_delay(self) -> float:
        """Returns the base delay in seconds for exponential back-off.

        Falls back to 0.5 seconds if the key is absent.

        :return: Base delay as a float number of seconds.
        """
        return self._config.getfloat(
            "retry", "base-delay", fallback=_DEFAULT_BASE_DELAY
        )

    def get_max_delay(self) -> float:
        """Returns the maximum delay cap in seconds for exponential back-off.

        Falls back to 10.0 seconds if the key is absent.

        :return: Maximum delay as a float number of seconds.
        """
        return self._config.getfloat("retry", "max-delay", fallback=_DEFAULT_MAX_DELAY)
