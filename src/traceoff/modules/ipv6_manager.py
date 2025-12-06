"""
IPv6 status and basic management module.

This module provides helpers to inspect whether IPv6 is
enabled system-wide and to temporarily enable or disable
it using sysctl. This is a privacy trade-off: disabling
IPv6 can reduce some leak vectors, but may impact services.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from ..core.config import TraceOffConfig
from ..core.exceptions import PrivilegeError
from ..core.logger import get_logger
from ..core.models import CheckResult, CheckStatus
from ..utils.shell import run_command

logger = get_logger(__name__)


@dataclass
class Ipv6Manager:
    """
    Inspect and modify IPv6 configuration.

    Attributes:
        config:
            Shared TraceOff configuration instance. Currently unused,
            but reserved for future policy or profile settings.
    """

    config: TraceOffConfig

    SYSCTL_PATH_ALL = "/proc/sys/net/ipv6/conf/all/disable_ipv6"
    SYSCTL_PATH_DEFAULT = "/proc/sys/net/ipv6/conf/default/disable_ipv6"

    @staticmethod
    def _require_root() -> None:
        """
        Ensure that the current process is running with root privileges.

        Raises:
            PrivilegeError:
                If effective user ID is not root.
        """
        if os.geteuid() != 0:
            raise PrivilegeError(
                "IPv6 enable/disable operations require root privileges."
            )

    def is_ipv6_available(self) -> bool:
        """
        Determine whether the system has IPv6 support enabled.

        Returns:
            True if IPv6 appears available, False otherwise.

        Notes:
            This is a heuristic based on the presence of sysctl
            files used by the Linux kernel.
        """
        return os.path.exists(self.SYSCTL_PATH_ALL)

    def is_ipv6_disabled(self) -> bool:
        """
        Check whether IPv6 is currently disabled system-wide.

        Returns:
            True if IPv6 appears disabled, False otherwise.
        """
        if not self.is_ipv6_available():
            return False

        try:
            with open(self.SYSCTL_PATH_ALL, "r", encoding="utf-8") as fh:
                value = fh.read().strip()
            return value == "1"
        except OSError as exc:
            logger.debug("Failed to read IPv6 disable state: %s", exc)
            return False

    def build_status_check(self) -> CheckResult:
        """
        Build a CheckResult describing the current IPv6 status.

        Returns:
            CheckResult with INFO/WARNING status depending on configuration.
        """
        if not self.is_ipv6_available():
            summary = "IPv6 does not appear to be available on this system."
            status = CheckStatus.INFO
            disabled = None
        else:
            disabled = self.is_ipv6_disabled()
            if disabled:
                summary = "IPv6 is currently disabled system-wide."
                status = CheckStatus.INFO
            else:
                summary = "IPv6 is enabled system-wide. This may slightly increase leak surface."
                status = CheckStatus.INFO

        return CheckResult(
            name="ipv6_status",
            status=status,
            summary=summary,
            details={"ipv6_disabled": disabled},
        )

    def disable_ipv6(self, dry_run: bool = False) -> None:
        """
        Temporarily disable IPv6 via sysctl.

        Args:
            dry_run:
                If True, show the commands that would be executed but
                do not actually change the system.

        Raises:
            PrivilegeError:
                If called without root privileges.
        """
        self._require_root()

        if not self.is_ipv6_available():
            logger.info("IPv6 does not appear to be available; nothing to disable.")
            return

        logger.info("Disabling IPv6 system-wide (dry_run=%s)...", dry_run)
        commands: List[List[str]] = [
            ["sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=1"],
            ["sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=1"],
        ]
        for cmd in commands:
            run_command(cmd, dry_run=dry_run)

    def enable_ipv6(self, dry_run: bool = False) -> None:
        """
        Temporarily enable IPv6 via sysctl.

        Args:
            dry_run:
                If True, show the commands that would be executed but
                do not actually change the system.

        Raises:
            PrivilegeError:
                If called without root privileges.
        """
        self._require_root()

        if not self.is_ipv6_available():
            logger.info("IPv6 does not appear to be available; nothing to enable.")
            return

        logger.info("Enabling IPv6 system-wide (dry_run=%s)...", dry_run)
        commands: List[List[str]] = [
            ["sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=0"],
            ["sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=0"],
        ]
        for cmd in commands:
            run_command(cmd, dry_run=dry_run)
