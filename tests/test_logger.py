"""Tests for src.utils.logger module."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import pytest
from src.utils.logger import setup_logger


class TestSetupLogger:
    """Tests for setup_logger."""

    def test_returns_logger(self):
        logger = setup_logger("test_logger_basic")
        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        logger = setup_logger("my_custom_logger")
        assert logger.name == "my_custom_logger"

    def test_default_level_is_info(self):
        logger = setup_logger("test_level_default")
        assert logger.level == logging.INFO

    def test_custom_level(self):
        logger = setup_logger("test_level_debug", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_has_handler(self):
        logger = setup_logger("test_handler")
        assert len(logger.handlers) >= 1

    def test_handler_is_stream_handler(self):
        logger = setup_logger("test_stream_handler")
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1

    def test_handler_has_formatter(self):
        logger = setup_logger("test_formatter")
        handler = logger.handlers[-1]
        assert handler.formatter is not None
        # Check format contains expected fields
        fmt = handler.formatter._fmt
        assert "%(name)s" in fmt
        assert "%(levelname)s" in fmt
        assert "%(message)s" in fmt

    def test_logger_can_log(self, capsys):
        logger = setup_logger("test_can_log")
        logger.info("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.out
