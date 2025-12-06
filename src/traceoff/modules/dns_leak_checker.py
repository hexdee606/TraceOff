"""
DNS leak checking module.

This module inspects `/etc/resolv.conf` to identify configured
DNS servers and uses simple heuristics plus VPN-like interface
detection to assess potential privacy risks.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import List

from ..core.config import TraceOffConfig
from ..core.logger import get_logger
from ..core.models import DnsConfig, CheckResult, CheckStatus
from ..utils.network import detect_vpn_like_interfaces

logger = get_logger(__name__)


@dataclass
class DnsLeakChecker:
    """
    Inspect DNS resolver configuration for potential leaks.

    Attributes:
        config:
            Shared TraceOff configuration instance. Currently unused,
            but reserved for future DNS-related settings.
    """

    config: TraceOffConfig

    RESOLV_CONF_PATH = "/etc/resolv.conf"

    def _parse_resolv_conf(self) -> List[str]:
        """
        Parse /etc/resolv.conf and collect nameserver entries.

        Returns:
            List of DNS server IP addresses.
        """
        servers: List[str] = []
        try:
            with open(self.RESOLV_CONF_PATH, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("nameserver"):
                        parts = line.split()
                        if len(parts) >= 2:
                            servers.append(parts[1])
        except FileNotFoundError:
            logger.warning("%s not found. DNS servers could not be inspected.", self.RESOLV_CONF_PATH)
        except OSError as exc:
            logger.warning("Failed to read %s: %s", self.RESOLV_CONF_PATH, exc)
        return servers

    @staticmethod
    def _is_private_ip(ip_str: str) -> bool:
        """
        Determine whether the given IP address is private (RFC1918 or similar).

        Args:
            ip_str:
                String representation of an IP address.

        Returns:
            True if the address is private, False otherwise.
        """
        try:
            ip_obj = ip_address(ip_str)
            return ip_obj.is_private
        except ValueError:
            return False

    def build_dns_config(self) -> DnsConfig:
        """
        Build a DnsConfig instance representing current DNS setup.

        Returns:
            DnsConfig with resolver list and VPN-like detection.

        Notes:
            VPN detection is heuristic and based on interface names
            like 'tun0', 'wg0', 'ppp0'. It does not guarantee VPN is
            actually active.
        """
        servers = self._parse_resolv_conf()
        vpn_ifaces = detect_vpn_like_interfaces()
        vpn_detected = bool(vpn_ifaces)

        return DnsConfig(
            servers=servers,
            vpn_detected=vpn_detected,
            vpn_interfaces=vpn_ifaces,
        )

    def build_check_result(self) -> CheckResult:
        """
        Create a CheckResult describing DNS leak risk.

        Returns:
            CheckResult with status and details on DNS configuration.
        """
        dns_cfg = self.build_dns_config()
        servers = dns_cfg.servers

        if not servers:
            summary = "No DNS servers found in /etc/resolv.conf."
            status = CheckStatus.INFO
        else:
            # Simple heuristic: if VPN-like interface exists but DNS servers
            # are public (not private IPs), warn that DNS may bypass VPN.
            has_vpn = dns_cfg.vpn_detected
            private_flags = [self._is_private_ip(s) for s in servers]
            any_private = any(private_flags)

            if has_vpn and not any_private:
                summary = "VPN-like interface detected but DNS servers look public; possible DNS leak."
                status = CheckStatus.WARNING
            else:
                summary = f"{len(servers)} DNS server(s) configured."
                status = CheckStatus.INFO

        details = {
            "servers": servers,
            "vpn_detected": dns_cfg.vpn_detected,
            "vpn_interfaces": dns_cfg.vpn_interfaces,
        }

        return CheckResult(
            name="dns_leak",
            status=status,
            summary=summary,
            details=details,
        )

    def build_human_summary(self) -> str:
        """
        Build a human-readable DNS configuration summary.

        Returns:
            Multiline string summarizing DNS servers and VPN hints.
        """
        result = self.build_check_result()
        lines: List[str] = []
        lines.append("=== TraceOff: DNS Configuration Summary ===")
        lines.append(result.summary)
        lines.append("")

        servers = result.details.get("servers", [])
        if servers:
            lines.append("DNS Servers:")
            for s in servers:
                lines.append(f"  - {s}")
        else:
            lines.append("DNS Servers: <none found>")

        lines.append("")
        lines.append(f"VPN-like interfaces: {', '.join(result.details.get('vpn_interfaces', [])) or '<none>'}")
        lines.append(f"VPN detected: {result.details.get('vpn_detected', False)}")

        return "\n".join(lines)
