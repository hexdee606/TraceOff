"""
Auto-fix engine for TraceOff.

Evaluates privacy risks and offers guided remediation
based on registered check results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..core.logger import get_logger
from ..core.models import CheckResult, CheckStatus
from ..checks.registry import registry

# Modules capable of remediation
from .mac_manager import MacManager
from .ipv6_manager import Ipv6Manager
from .firewall_manager import FirewallManager

logger = get_logger(__name__)


@dataclass
class AutoFixOption:
    """Represents a possible system fix."""
    name: str
    description: str
    action: callable


class AutoFixManager:

    def __init__(self, config):
        self.config = config
        self.options: List[AutoFixOption] = []

    def evaluate(self) -> List[AutoFixOption]:
        """Analyze privacy report and decide which actions are needed."""
        report = registry.run_all()

        for r in report.results:
            if r.name == "mac_exposure" and r.status in {CheckStatus.WARNING, CheckStatus.CRITICAL}:
                self.options.append(
                    AutoFixOption(
                        name="mac_spoof",
                        description="Randomize your MAC address to avoid tracking.",
                        action=lambda: MacManager(self.config).change_mac_once("wlan0")
                    )
                )

            if r.name == "ipv6_status" and r.status == CheckStatus.WARNING:
                self.options.append(
                    AutoFixOption(
                        name="disable_ipv6",
                        description="IPv6 may leak identity — disable it temporarily.",
                        action=lambda: Ipv6Manager(self.config).disable_ipv6()
                    )
                )

            if r.name == "firewall_status" and r.status != CheckStatus.OK:
                self.options.append(
                    AutoFixOption(
                        name="enable_firewall",
                        description="Enable firewall protections with UFW.",
                        action=lambda: FirewallManager(self.config).apply_profile("public")
                    )
                )

        return self.options

    def run_interactive(self):
        """Prompt user before applying fixes."""
        fixes = self.evaluate()

        if not fixes:
            print("✔ No fixes required — your configuration looks safe.")
            return

        print("⚠ Privacy improvements available:\n")

        for fix in fixes:
            choice = input(f"→ {fix.description}  Apply? [Y/n]: ").strip().lower()
            if choice in {"", "y", "yes"}:
                print(f"🔧 Applying: {fix.name}...")
                fix.action()
                print("✔ Done.\n")
            else:
                print("⏭ Skipped.\n")
