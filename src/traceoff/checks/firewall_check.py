"""
Privacy check for firewall status using UFW.
"""

from __future__ import annotations

from .base import OptionalDependencyCheck
from .registry import registry
from ..core.config import TraceOffConfig
from ..core.models import CheckResult, CheckStatus
from ..modules.firewall_manager import FirewallManager


class FirewallStatusCheck(OptionalDependencyCheck):
    """
    Inspect firewall status via UFW.

    If UFW is not installed or accessible, the check will
    be reported as informational rather than failing.
    """

    name = "firewall_status"
    description = "Check firewall status using UFW."

    def run(self) -> CheckResult:
        """
        Run the firewall status check.

        Returns:
            CheckResult summarizing firewall status.
        """
        config = TraceOffConfig.load_or_default()
        mgr = FirewallManager(config=config)
        status_text = mgr.get_status().strip()

        if "unavailable" in status_text.lower():
            return self.skip("UFW not installed or firewall status unavailable.")

        # Basic heuristic: look for 'Status: active' in ufw output.
        is_active = "Status: active" in status_text

        status = CheckStatus.INFO
        summary = "Firewall appears inactive."
        if is_active:
            status = CheckStatus.OK
            summary = "Firewall appears active (UFW)."

        return CheckResult(
            name=self.name,
            status=status,
            summary=summary,
            details={
                "raw_status": status_text,
                "active": is_active,
            },
        )


registry.register(FirewallStatusCheck)
