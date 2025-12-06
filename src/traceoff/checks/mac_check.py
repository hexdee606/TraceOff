"""
Privacy check for MAC address configuration.

This check inspects whether interfaces appear to be using
globally-administered vendor MACs (more persistent identity)
or locally-administered addresses (often randomized).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .base import PrivacyCheck
from .registry import registry
from ..core.models import CheckResult, CheckStatus
from ..utils.network import list_network_interfaces
from ..core.logger import get_logger

logger = get_logger(__name__)


class MacExposureCheck(PrivacyCheck):
    """
    Inspect network interfaces for MAC address exposure risk.
    """

    name = "mac_exposure"
    description = "Check if interfaces use persistent vendor MACs or randomized MACs."

    def _read_mac(self, iface: str) -> Optional[str]:
        """
        Read the MAC address for a given interface from /sys.

        Args:
            iface:
                Name of the network interface.

        Returns:
            MAC address string, or None if unavailable.
        """
        addr_path = Path("/sys/class/net") / iface / "address"
        try:
            return addr_path.read_text(encoding="utf-8").strip()
        except Exception as exc:
            logger.debug("Failed to read MAC for %s: %s", iface, exc)
            return None

    @staticmethod
    def _is_locally_administered(mac: str) -> bool:
        """
        Determine whether a MAC address is locally-administered.

        Args:
            mac:
                MAC address string in 'aa:bb:cc:dd:ee:ff' form.

        Returns:
            True if the locally-administered bit is set, False otherwise.
        """
        try:
            first_octet_str = mac.split(":")[0]
            first_octet = int(first_octet_str, 16)
            # Locally-administered bit is bit 1 of the first octet.
            return bool(first_octet & 0b00000010)
        except Exception:
            return False

    def run(self) -> CheckResult:
        """
        Run the MAC exposure check.

        Returns:
            CheckResult summarizing MAC exposure risks.
        """
        interfaces = list_network_interfaces()
        if not interfaces:
            return CheckResult(
                name=self.name,
                status=CheckStatus.INFO,
                summary="No non-loopback interfaces found to inspect MAC addresses.",
                details={"interfaces": []},
            )

        info: List[Dict[str, object]] = []
        global_mac_count = 0
        local_mac_count = 0

        for iface in interfaces:
            mac = self._read_mac(iface)
            if mac is None:
                info.append({"interface": iface, "mac": None, "locally_administered": None})
                continue

            is_local = self._is_locally_administered(mac)
            if is_local:
                local_mac_count += 1
            else:
                global_mac_count += 1

            info.append(
                {
                    "interface": iface,
                    "mac": mac,
                    "locally_administered": is_local,
                }
            )

        status = CheckStatus.INFO
        if global_mac_count > 0:
            status = CheckStatus.WARNING
            summary = (
                f"{global_mac_count} interface(s) use globally-administered vendor MACs; "
                "consider MAC spoofing on untrusted networks."
            )
        else:
            summary = "All inspected interfaces appear to use locally-administered MACs."

        return CheckResult(
            name=self.name,
            status=status,
            summary=summary,
            details={
                "interfaces": info,
                "global_mac_count": global_mac_count,
                "local_mac_count": local_mac_count,
            },
        )


registry.register(MacExposureCheck)
