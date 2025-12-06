"""
Privacy check for Wi-Fi auto-connect behaviour and known networks.
"""

from __future__ import annotations

from typing import List

from .base import OptionalDependencyCheck
from .registry import registry
from ..core.config import TraceOffConfig
from ..core.models import CheckResult, CheckStatus
from ..modules.wifi_privacy import WifiPrivacyManager


class WifiPrivacyCheck(OptionalDependencyCheck):
    """
    Inspect known Wi-Fi networks and auto-connect settings.

    Relies on NetworkManager's `nmcli` tool. If nmcli is not
    available, the check is skipped gracefully.
    """

    name = "wifi_privacy"
    description = "Check Wi-Fi known networks and auto-connect risks."

    def run(self) -> CheckResult:
        """
        Run the Wi-Fi privacy check.

        Returns:
            CheckResult summarizing known Wi-Fi networks and auto-connect usage.
        """
        config = TraceOffConfig.load_or_default()
        mgr = WifiPrivacyManager(config=config)

        # Try listing networks; manager will handle nmcli absence internally.
        networks = mgr.list_known_networks()

        if not networks:
            # Could be no networks, or nmcli missing. For now, treat as info.
            return CheckResult(
                name=self.name,
                status=CheckStatus.INFO,
                summary="No Wi-Fi networks found or NetworkManager not available.",
                details={
                    "known_networks": 0,
                    "autoconnect_count": 0,
                },
            )

        auto_count = sum(1 for n in networks if n.autoconnect)
        status = CheckStatus.INFO
        summary = f"{len(networks)} known Wi-Fi networks, {auto_count} auto-connect enabled."

        # Simple heuristic: many auto-connect networks → slightly higher risk.
        if auto_count > 5:
            status = CheckStatus.WARNING
            summary += " Many auto-connect networks may increase tracking surface."

        return CheckResult(
            name=self.name,
            status=status,
            summary=summary,
            details={
                "known_networks": len(networks),
                "autoconnect_count": auto_count,
                "networks": [
                    {"name": n.name, "ssid": n.ssid, "autoconnect": n.autoconnect}
                    for n in networks
                ],
            },
        )


registry.register(WifiPrivacyCheck)
