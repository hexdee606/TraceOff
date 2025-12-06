"""
Privacy check for public IP and basic GeoIP exposure.
"""

from __future__ import annotations

from .base import PrivacyCheck
from .registry import registry
from ..core.config import TraceOffConfig
from ..core.models import CheckResult
from ..modules.ip_leak_checker import IpLeakChecker


class IpLeakCheck(PrivacyCheck):
    """
    Check current public IP address and approximate location.
    """

    name = "ip_leak"
    description = "Check public IP address and approximate location exposure."

    def run(self) -> CheckResult:
        """
        Run the IP leak check.

        Returns:
            CheckResult describing current public IP and location.
        """
        config = TraceOffConfig.load_or_default()
        checker = IpLeakChecker(config=config)
        return checker.build_check_result()


# Register this check in the global registry.
registry.register(IpLeakCheck)
