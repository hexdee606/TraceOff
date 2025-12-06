"""
Wi-Fi privacy helper module.

This module provides helpers around remembered Wi-Fi networks
and auto-connect behaviour. It currently focuses on read-only
inspection via NetworkManager (`nmcli`), which is common on
desktop Linux distributions, including many security-focused
ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..core.config import TraceOffConfig
from ..core.logger import get_logger
from ..utils.shell import run_command

logger = get_logger(__name__)


@dataclass
class WifiNetworkInfo:
    """
    Basic information about a known Wi-Fi network.

    Attributes:
        name:
            Connection name in NetworkManager (may differ from SSID).
        ssid:
            SSID of the Wi-Fi network, if available.
        autoconnect:
            Whether NetworkManager is configured to auto-connect.
    """

    name: str
    ssid: Optional[str]
    autoconnect: bool


@dataclass
class WifiPrivacyManager:
    """
    Manage Wi-Fi related privacy inspection.

    Attributes:
        config:
            Shared TraceOff configuration instance.
    """

    config: TraceOffConfig

    def _nmcli_exists(self) -> bool:
        """
        Check whether the `nmcli` command is available on the system.

        Returns:
            True if nmcli is found in PATH, False otherwise.
        """
        try:
            run_command(["nmcli", "-v"], check=False)
            return True
        except Exception:
            logger.debug("nmcli not available on this system.")
            return False

    def list_known_networks(self) -> List[WifiNetworkInfo]:
        """
        List known Wi-Fi networks managed by NetworkManager.

        Returns:
            List of WifiNetworkInfo objects. If NetworkManager is not
            present or the command fails, the list may be empty.

        Notes:
            This function is intentionally conservative: if anything
            unexpected happens, it returns an empty list rather than
            raising, so callers can degrade gracefully.
        """
        if not self._nmcli_exists():
            return []

        # Use tab-separated fields for easier parsing.
        fields = "NAME,TYPE,AUTOCONNECT,DEVICE"
        cmd = ["nmcli", "-t", "connection", "show", f"connection.type=wifi", f"connection.autoconnect"]
        # Above filter style can vary between versions; to keep it simple:
        cmd = ["nmcli", "-t", "connection", "show"]

        try:
            proc = run_command(cmd, check=False)
        except Exception as exc:
            logger.debug("Failed to run nmcli connection show: %s", exc)
            return []

        networks: List[WifiNetworkInfo] = []
        for line in proc.stdout.splitlines():
            # Typical `nmcli -t connection show` format:
            # NAME:UUID:TYPE:DEVICE
            parts = line.strip().split(":")
            if len(parts) < 4:
                continue
            name, _uuid, ctype, device = parts[:4]
            if ctype != "wifi":
                continue

            # Determine autoconnect flag for this connection.
            autoconnect = self._get_autoconnect_flag(name)
            ssid = self._get_ssid_for_connection(name)

            networks.append(
                WifiNetworkInfo(
                    name=name,
                    ssid=ssid,
                    autoconnect=autoconnect,
                )
            )

        return networks

    def _get_autoconnect_flag(self, connection_name: str) -> bool:
        """
        Query NetworkManager for the autoconnect flag of a connection.

        Args:
            connection_name:
                Name of the NetworkManager connection.

        Returns:
            True if autoconnect is enabled, False otherwise.
        """
        try:
            proc = run_command(
                ["nmcli", "-g", "connection.autoconnect", "connection", "show", connection_name],
                check=False,
            )
            value = proc.stdout.strip().lower()
            return value == "yes"
        except Exception as exc:
            logger.debug("Failed to read autoconnect for %s: %s", connection_name, exc)
            return False

    def _get_ssid_for_connection(self, connection_name: str) -> Optional[str]:
        """
        Query NetworkManager for the SSID associated with a connection.

        Args:
            connection_name:
                Name of the NetworkManager connection.

        Returns:
            SSID string if available, otherwise None.
        """
        # Some systems store SSID in 802-11-wireless.ssid
        try:
            proc = run_command(
                ["nmcli", "-g", "802-11-wireless.ssid", "connection", "show", connection_name],
                check=False,
            )
            ssid = proc.stdout.strip()
            return ssid or None
        except Exception as exc:
            logger.debug("Failed to read SSID for %s: %s", connection_name, exc)
            return None

    def build_human_summary(self) -> str:
        """
        Build a human-readable summary of known Wi-Fi networks and
        auto-connect behaviour.

        Returns:
            Multiline string summarizing Wi-Fi privacy exposure.
        """
        networks = self.list_known_networks()
        lines: List[str] = []
        lines.append("=== TraceOff: Wi-Fi Privacy Summary ===")

        if not networks:
            lines.append("No Wi-Fi networks found via NetworkManager (or nmcli not available).")
            return "\n".join(lines)

        auto_count = sum(1 for n in networks if n.autoconnect)
        lines.append(f"Known Wi-Fi networks: {len(networks)}")
        lines.append(f"Auto-connect enabled: {auto_count}")
        lines.append("")

        for n in networks:
            lines.append(f"- Name: {n.name}")
            lines.append(f"  SSID: {n.ssid or '<unknown>'}")
            lines.append(f"  Autoconnect: {n.autoconnect}")
            lines.append("")

        if auto_count > 5:
            lines.append(
                "Note: Many auto-connecting Wi-Fi networks can increase your tracking surface "
                "when moving between locations."
            )

        return "\n".join(lines)
