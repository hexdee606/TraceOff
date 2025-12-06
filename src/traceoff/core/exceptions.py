"""
Custom exception types used across TraceOff.

Defining dedicated exception classes makes it easier to
handle expected error conditions gracefully in the CLI
and keep internal logic clear.
"""

from __future__ import annotations

from typing import Optional


class TraceOffError(Exception):
    """
    Base exception class for TraceOff-specific errors.
    """


class PrivilegeError(TraceOffError):
    """
    Raised when an operation requires elevated privileges.

    For example, changing MAC addresses, modifying firewall
    rules or toggling IPv6 typically require root access.
    """


class CommandExecutionError(TraceOffError):
    """
    Raised when a system command executed by TraceOff fails.

    Attributes:
        stderr:
            Optional stderr output from the failed command, used
            to provide more helpful error messages to the user.
    """

    def __init__(self, message: str, *, stderr: Optional[str] = None) -> None:
        super().__init__(message)
        self.stderr: Optional[str] = stderr


class ConfigError(TraceOffError):
    """
    Raised when configuration values are invalid or missing
    in a way that prevents normal operation.
    """
