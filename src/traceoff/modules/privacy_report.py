"""
Privacy report aggregation module.

This module combines multiple checks (IP, DNS, IPv6, Wi-Fi,
hostname, MAC, firewall, etc.) to provide a unified view
of the user's privacy posture at a given moment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

from ..core.config import TraceOffConfig
from ..core.logger import get_logger
from ..core.models import PrivacyReport, CheckStatus
from ..checks.registry import registry

# Import check modules so they register themselves with the registry.
# The imports are used for side effects (registration).
from ..checks import (  # noqa: F401
    ip_check,
    dns_check,
    ipv6_check,
    wifi_check,
    hostname_check,
    firewall_check,
    mac_check,
)

logger = get_logger(__name__)


@dataclass
class PrivacyReportBuilder:
    """
    Build comprehensive privacy reports.

    Attributes:
        config:
            Shared TraceOff configuration instance. Currently not passed
            directly into checks; each check loads configuration as needed.
    """

    config: TraceOffConfig

    def build_report(self) -> PrivacyReport:
        """
        Generate a structured privacy report aggregating all registered checks.

        Returns:
            PrivacyReport containing a list of CheckResult items.
        """
        logger.debug("Building privacy report via registered checks.")
        return registry.run_all()

    def render_human_readable(self) -> str:
        """
        Render the privacy report as a human-readable multiline string.

        Returns:
            Multiline string summarizing all checks and a small status summary.
        """
        report = self.build_report()
        lines: List[str] = []
        lines.append("=== TraceOff: Privacy Checkup Report ===")
        lines.append("")

        for result in report.results:
            lines.append(f"[{result.status.value.upper()}] {result.name}")
            lines.append(f"  {result.summary}")
            if result.details:
                lines.append(f"  details: {result.details}")
            lines.append("")

        # Summary at the bottom.
        counts = report.summary_counts()
        lines.append("Summary:")
        for status in CheckStatus:
            lines.append(f"  {status.value}: {counts.get(status, 0)}")

        return "\n".join(lines)

    def render_json(self, indent: int = 2) -> str:
        """
        Render the privacy report as a JSON string.

        Args:
            indent:
                Number of spaces to use for JSON indentation.

        Returns:
            JSON-formatted string representing the report.
        """
        report = self.build_report()
        data = report.to_dict()
        return json.dumps(data, indent=indent)
