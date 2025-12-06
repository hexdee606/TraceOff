"""
Privacy check for hostname and mDNS (Avahi) exposure.
"""

from __future__ import annotations

from .base import PrivacyCheck
from .registry import registry
from ..core.config import TraceOffConfig
from ..core.models import CheckResult, CheckStatus
from ..modules.hostname_manager import HostnameManager


class HostnameExposureCheck(PrivacyCheck):
    """
    Inspect hostname and whether Avahi/mDNS broadcasting is active.
    """

    name = "hostname_exposure"
    description = "Check hostname and mDNS (Avahi) exposure on local networks."

    def run(self) -> CheckResult:
        """
        Run the hostname exposure check.

        Returns:
            CheckResult describing hostname and mDNS exposure.
        """
        config = TraceOffConfig.load_or_default()
        mgr = HostnameManager(config=config)
        info = mgr.get_info()

        status = CheckStatus.INFO
        summary_parts = [f"Hostname: {info.hostname}"]

        if info.avahi_running:
            status = CheckStatus.WARNING
            summary_parts.append("Avahi/mDNS is running and may broadcast the hostname.")

        summary = " | ".join(summary_parts)

        return CheckResult(
            name=self.name,
            status=status,
            summary=summary,
            details={
                "hostname": info.hostname,
                "fqdn": info.fqdn,
                "avahi_running": info.avahi_running,
            },
        )


registry.register(HostnameExposureCheck)
