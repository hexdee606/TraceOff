"""
Hostname and mDNS exposure module.

This module inspects the system hostname and checks whether
mDNS/Avahi is running, as these can reveal identifying
information (usernames, device names) on local networks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..core.config import TraceOffConfig
from ..core.logger import get_logger
from ..utils.shell import run_command

logger = get_logger(__name__)


@dataclass
class HostnameInfo:
    """
    Basic information about the system hostname and mDNS.

    Attributes:
        hostname:
            The system hostname as reported by /etc/hostname or uname.
        avahi_running:
            Whether the avahi-daemon service appears to be running.
        fqdn:
            Optional fully-qualified domain name, if resolvable.
    """

    hostname: str
    avahi_running: bool
    fqdn: Optional[str]


@dataclass
class HostnameManager:
    """
    Inspect hostname-related privacy aspects.

    Attributes:
        config:
            Shared TraceOff configuration instance.
    """

    config: TraceOffConfig

    HOSTNAME_PATH = "/etc/hostname"

    def get_hostname(self) -> str:
        """
        Obtain the system hostname.

        Returns:
            Hostname string as read from /etc/hostname, falling back
            to `os.uname().nodename` on failure.
        """
        try:
            return Path(self.HOSTNAME_PATH).read_text(encoding="utf-8").strip()
        except Exception as exc:
            logger.debug("Failed to read %s: %s", self.HOSTNAME_PATH, exc)
            return os.uname().nodename

    def is_avahi_running(self) -> bool:
        """
        Check whether the avahi-daemon service appears to be active.

        Returns:
            True if avahi-daemon is reported as active by systemctl,
            False otherwise.
        """
        try:
            proc = run_command(
                ["systemctl", "is-active", "avahi-daemon"],
                check=False,
            )
            return proc.stdout.strip() == "active"
        except Exception as exc:
            logger.debug("Failed to check avahi-daemon status: %s", exc)
            return False

    def get_fqdn(self) -> Optional[str]:
        """
        Attempt to determine the fully qualified domain name (FQDN).

        Returns:
            FQDN string if resolvable, otherwise None.
        """
        try:
            proc = run_command(["hostname", "-f"], check=False)
            fqdn = proc.stdout.strip()
            return fqdn or None
        except Exception as exc:
            logger.debug("Failed to read FQDN: %s", exc)
            return None

    def get_info(self) -> HostnameInfo:
        """
        Gather hostname and mDNS-related information.

        Returns:
            HostnameInfo instance.
        """
        hostname = self.get_hostname()
        avahi_running = self.is_avahi_running()
        fqdn = self.get_fqdn()
        return HostnameInfo(
            hostname=hostname,
            avahi_running=avahi_running,
            fqdn=fqdn,
        )

    def build_human_summary(self) -> str:
        """
        Build a human-readable summary of hostname and mDNS exposure.

        Returns:
            Multiline string summarizing hostname-related privacy aspects.
        """
        info = self.get_info()
        lines = []
        lines.append("=== TraceOff: Hostname Exposure Summary ===")
        lines.append(f"Hostname: {info.hostname}")
        lines.append(f"FQDN:     {info.fqdn or '<unknown>'}")
        lines.append(f"Avahi (mDNS) running: {info.avahi_running}")
        lines.append("")

        # Very simple heuristic: hostnames containing user-like fragments.
        hostname_lower = info.hostname.lower()
        if any(token in hostname_lower for token in ["user", "admin", "home", "office"]):
            lines.append(
                "Note: Your hostname appears to contain potentially identifying words "
                "(e.g. 'user', 'admin', 'home')."
            )

        if info.avahi_running:
            lines.append(
                "Note: Avahi/mDNS may broadcast your hostname on local networks. "
                "This can be useful but has privacy implications."
            )

        return "\n".join(lines)
