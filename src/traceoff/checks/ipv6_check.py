"""
Privacy check for IPv6 status.
"""

from __future__ import annotations

from .base import PrivacyCheck
from .registry import registry
from ..core.config import TraceOffConfig
from ..core.models import CheckResult
from ..modules.ipv6_manager import Ipv6Manager


class Ipv6StatusCheck(PrivacyCheck):
    """
    Inspect whether IPv6 is enabled or disabled system-wide.
    """

    name = "ipv6_status"
    description = "Check whether IPv6 is enabled/disabled system-wide."

    def run(self) -> CheckResult:
        """
        Run the IPv6 status check.

        Returns:
            CheckResult describing IPv6 availability and status.
        """
        config = TraceOffConfig.load_or_default()
        mgr = Ipv6Manager(config=config)
        return mgr.build_status_check()


registry.register(Ipv6StatusCheck)
