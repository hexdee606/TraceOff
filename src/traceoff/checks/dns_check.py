"""
Privacy check for DNS resolver configuration and potential leaks.
"""

from __future__ import annotations

from .base import PrivacyCheck
from .registry import registry
from ..core.config import TraceOffConfig
from ..core.models import CheckResult
from ..modules.dns_leak_checker import DnsLeakChecker


class DnsLeakCheck(PrivacyCheck):
    """
    Inspect DNS configuration and highlight potential DNS leaks.
    """

    name = "dns_leak"
    description = "Check DNS servers and possible VPN DNS leaks."

    def run(self) -> CheckResult:
        """
        Run the DNS leak check.

        Returns:
            CheckResult describing DNS configuration and risk level.
        """
        config = TraceOffConfig.load_or_default()
        checker = DnsLeakChecker(config=config)
        return checker.build_check_result()


registry.register(DnsLeakCheck)
