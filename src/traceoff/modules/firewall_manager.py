"""
Firewall profile management module.

This module applies simple UFW-based firewall profiles suitable
for different environments (home, public hotspot, etc.).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from ..core.config import TraceOffConfig
from ..core.exceptions import PrivilegeError
from ..core.logger import get_logger
from ..utils.shell import run_command

logger = get_logger(__name__)


@dataclass
class FirewallManager:
    """
    Manage firewall profiles for TraceOff.

    Attributes:
        config:
            Shared TraceOff configuration instance.
    """

    config: TraceOffConfig

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
                "Firewall operations require root privileges. "
                "Please run this command with sudo or as root."
            )

    def apply_profile(self, profile_name: str, dry_run: bool = False) -> None:
        """
        Apply a named firewall profile using UFW.

        Args:
            profile_name:
                Name of the profile to apply (e.g. 'public', 'home').
            dry_run:
                If True, only log the commands that would be run.

        Notes:
            This implementation assumes that UFW is installed. If it's
            not, commands will fail with CommandExecutionError. Future
            versions may detect UFW presence or support other backends.
        """
        self._require_root()

        profile = profile_name.lower()
        logger.info("Applying firewall profile '%s' (dry_run=%s)...", profile, dry_run)

        commands: List[List[str]]

        if profile == "public":
            # Strict profile for public Wi-Fi / untrusted networks.
            commands = [
                ["ufw", "default", "deny", "incoming"],
                ["ufw", "default", "allow", "outgoing"],
                ["ufw", "enable"],
            ]
        elif profile == "home":
            # Slightly more permissive, allows SSH from LAN.
            commands = [
                ["ufw", "default", "deny", "incoming"],
                ["ufw", "default", "allow", "outgoing"],
                ["ufw", "allow", "22/tcp"],
                ["ufw", "enable"],
            ]
        else:
            logger.error("Unknown firewall profile: %s", profile_name)
            raise ValueError(f"Unknown firewall profile: {profile_name!r}")

        for cmd in commands:
            run_command(cmd, dry_run=dry_run)

    def get_status(self) -> str:
        """
        Retrieve firewall status via UFW.

        Returns:
            Output from `ufw status` or a friendly message on failure.
        """
        try:
            proc = run_command(["ufw", "status"], dry_run=False, check=False)
            return proc.stdout
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to get firewall status: %s", exc)
            return "Firewall status unavailable. Is 'ufw' installed and accessible?"
