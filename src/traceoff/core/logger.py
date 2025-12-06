"""
Logging helpers for TraceOff.

This module provides functions to configure and retrieve
loggers with consistent formatting and log levels.

Logging is intended to be simple and stderr-based so that
TraceOff can be used safely in scripts.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

# Internal flag to ensure we only configure logging once.
_CONFIGURED = False


def configure_logging(level: Optional[str] = None) -> None:
    """
    Configure the root TraceOff logger.

    This function should be called once early in application
    startup. If called multiple times, subsequent calls are
    ignored.

    Args:
        level: Optional log level name such as 'DEBUG', 'INFO',
            'WARNING', 'ERROR'. If not provided, the value is
            taken from the environment variable TRACEOFF_LOG_LEVEL
            or defaults to 'INFO'.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = level or os.getenv("TRACEOFF_LOG_LEVEL", "INFO")
    try:
        log_level = getattr(logging, level_name.upper())
    except AttributeError:
        log_level = logging.INFO

    logger = logging.getLogger("traceoff")
    logger.setLevel(log_level)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Optional logger name. If not provided, the root
            'traceoff' logger is returned.

    Returns:
        A Logger instance.
    """
    if not _CONFIGURED:
        # Configure with default level if not configured yet.
        configure_logging()

    if name is None:
        return logging.getLogger("traceoff")
    return logging.getLogger(name)
