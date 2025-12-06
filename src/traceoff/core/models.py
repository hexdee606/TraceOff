"""
Core data models used by TraceOff modules.

This module defines small, focused data structures for
representing things like public IP information, DNS
configuration and the results of privacy checks.

Using shared models keeps data flow consistent and helps
validation, testing and future refactoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class CheckStatus(str, Enum):
    """
    Status values for privacy and system checks.

    Attributes:
        OK:
            No significant issue detected.
        WARNING:
            Potentially concerning configuration or exposure.
        CRITICAL:
            Serious issue detected that should be fixed quickly.
        INFO:
            Informational result without clear risk.
    """

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    INFO = "info"


@dataclass
class LocationInfo:
    """
    Public IP location information.

    Attributes:
        ip:
            Public IPv4/IPv6 address as a string.
        country:
            Optional country code or name.
        region:
            Optional region/state name.
        city:
            Optional city name.
        asn:
            Optional autonomous system identifier or name.
        isp:
            Optional internet service provider name.
    """

    ip: str
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    asn: Optional[str] = None
    isp: Optional[str] = None


@dataclass
class DnsConfig:
    """
    DNS resolver configuration summary.

    Attributes:
        servers:
            List of DNS server IP addresses.
        vpn_detected:
            Whether a VPN-like interface appears to be active.
        vpn_interfaces:
            Names of interfaces that look like VPN tunnels.
    """

    servers: List[str] = field(default_factory=list)
    vpn_detected: bool = False
    vpn_interfaces: List[str] = field(default_factory=list)


@dataclass
class MacChangeResult:
    """
    Result of a MAC address change operation.

    Attributes:
        interface:
            Name of the interface whose MAC was changed.
        old_mac:
            Previous MAC address, if known.
        new_mac:
            New MAC address that was applied.
        dry_run:
            Whether the change was simulated (dry run) only.
    """

    interface: str
    old_mac: Optional[str]
    new_mac: str
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the MAC change result to a dictionary.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "interface": self.interface,
            "old_mac": self.old_mac,
            "new_mac": self.new_mac,
            "dry_run": self.dry_run,
        }


@dataclass
class CheckResult:
    """
    Generic result from a privacy or system check.

    Attributes:
        name:
            Short identifier of the check (e.g. 'ip_leak', 'dns_leak').
        status:
            Overall status of the check (ok/warning/critical/info).
        summary:
            Human-readable one-line summary.
        details:
            Machine-readable details for reporting or automation.
    """

    name: str
    status: CheckStatus
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the check result to a dictionary suitable for JSON/YAML.

        Returns:
            Dictionary representation of the check result.
        """
        return {
            "name": self.name,
            "status": self.status.value,
            "summary": self.summary,
            "details": self.details,
        }


@dataclass
class PrivacyReport:
    """
    Aggregated privacy report.

    Attributes:
        results:
            List of individual check results.
    """

    results: List[CheckResult] = field(default_factory=list)

    def add_result(self, result: CheckResult) -> None:
        """
        Append a new check result to the report.

        Args:
            result:
                The CheckResult instance to append.
        """
        self.results.append(result)

    def summary_counts(self) -> Dict[CheckStatus, int]:
        """
        Count how many results have each status.

        Returns:
            Dictionary mapping CheckStatus to number of results.
        """
        counts: Dict[CheckStatus, int] = {
            CheckStatus.OK: 0,
            CheckStatus.WARNING: 0,
            CheckStatus.CRITICAL: 0,
            CheckStatus.INFO: 0,
        }
        for r in self.results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the privacy report to a dictionary.

        Returns:
            Dictionary with a list of check result dictionaries and a
            summary of status counts.
        """
        return {
            "results": [r.to_dict() for r in self.results],
            "summary": {
                status.value: count for status, count in self.summary_counts().items()
            },
        }
