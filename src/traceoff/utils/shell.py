"""
Utility helpers for running shell commands safely.

All system-dependent operations should pass through this
module to centralize logging, error handling and dry-run
behaviour. This makes it easier to audit what TraceOff is
doing and to test command construction logic.
"""

from __future__ import annotations

import shlex
import subprocess
from typing import List

from ..core.exceptions import CommandExecutionError
from ..core.logger import get_logger

logger = get_logger(__name__)


def run_command(
        command: List[str],
        dry_run: bool = False,
        check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """
    Execute a system command with logging and error handling.

    Args:
        command:
            List of arguments that form the command. The first element
            should be the executable, followed by its arguments.
        dry_run:
            If True, the command will be logged but not executed. A
            dummy successful CompletedProcess is returned instead.
        check:
            If True, non-zero exit codes will raise CommandExecutionError.
            If False, the return code is left to the caller to inspect.

    Returns:
        A CompletedProcess instance representing the result of the command.

    Raises:
        CommandExecutionError:
            If `check` is True and the command exits with a non-zero status.
    """
    printable = " ".join(shlex.quote(arg) for arg in command)
    logger.debug("Executing command: %s (dry_run=%s)", printable, dry_run)

    if dry_run:
        # In dry-run mode, do not execute; return a dummy result.
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="DRY RUN: " + printable + "\n",
            stderr="",
        )

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if check and process.returncode != 0:
        stderr_clean = (process.stderr or "").strip()
        logger.error("Command failed: %s", printable)
        if stderr_clean:
            logger.error("stderr: %s", stderr_clean)
        raise CommandExecutionError(
            f"Command '{printable}' failed with exit code {process.returncode}",
            stderr=stderr_clean or None,
        )

    stdout_clean = (process.stdout or "").strip()
    stderr_clean = (process.stderr or "").strip()

    if stdout_clean:
        logger.debug("stdout: %s", stdout_clean)
    if stderr_clean:
        logger.debug("stderr: %s", stderr_clean)

    return process
