"""
tests.test_config - Unit tests for the vulguard.config module.

:author: Ron Webb
:since: 1.0.0
"""

import os
import tempfile
from unittest.mock import patch

from vulguard.config import Config, _DEFAULT_MODEL, _DEFAULT_TIMEOUT


class TestConfig:
    """Unit tests for the Config class.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_get_model_returns_configured_value(self) -> None:
        """Config.get_model() returns the value from config.ini."""
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "config.ini")
            with open(config_path, "w", encoding="utf-8") as ini:
                ini.write("[model]\nmodel = gpt-4o\ntimeout = 60\n")
            with patch("vulguard.config.CONF_DIR", tmp):
                cfg = Config()
                assert cfg.get_model() == "gpt-4o"

    def test_get_timeout_returns_configured_value(self) -> None:
        """Config.get_timeout() returns the integer value from config.ini."""
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "config.ini")
            with open(config_path, "w", encoding="utf-8") as ini:
                ini.write("[model]\nmodel = gpt-4o\ntimeout = 120\n")
            with patch("vulguard.config.CONF_DIR", tmp):
                cfg = Config()
                assert cfg.get_timeout() == 120

    def test_get_model_returns_default_when_missing(self) -> None:
        """Config.get_model() falls back to the default when config.ini is absent."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vulguard.config.CONF_DIR", tmp):
                cfg = Config()
                assert cfg.get_model() == _DEFAULT_MODEL

    def test_get_timeout_returns_default_when_missing(self) -> None:
        """Config.get_timeout() falls back to the default when config.ini is absent."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vulguard.config.CONF_DIR", tmp):
                cfg = Config()
                assert cfg.get_timeout() == _DEFAULT_TIMEOUT

    def test_get_timeout_returns_int(self) -> None:
        """Config.get_timeout() always returns an int, not a string."""
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "config.ini")
            with open(config_path, "w", encoding="utf-8") as ini:
                ini.write("[model]\nmodel = claude-sonnet-4.6\ntimeout = 500\n")
            with patch("vulguard.config.CONF_DIR", tmp):
                cfg = Config()
                assert isinstance(cfg.get_timeout(), int)
