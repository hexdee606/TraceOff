"""
Base classes and interfaces for TraceOff privacy checks.

This module defines the abstract structure for privacy checks.
Each check returns a standardized CheckResult so that reports
remain consistent regardless of the underlying check.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..core.models import CheckResult
from ..core.logger import get_logger

logger = get_logger(__name__)


class PrivacyCheck(ABC):
    """
    Abstract base class for a privacy check.

    A privacy check inspects some aspect of system configuration
    or network exposure (e.g., IP, DNS, IPv6, hostname, metadata).

    Subclasses should override:
        - `name` (short identifier)
        - `description` (short human-readable description)
        - `run()` (implementation)
    """

    #: Short identifier for the check (e.g. "ip_leak").
    name: str = "unnamed"
    #: Human-readable description of what the check does.
    description: str = ""

    @abstractmethod
    def run(self) -> CheckResult:
        """
        Execute the privacy check and return a CheckResult.

        Each concrete check must implement this method.
        """
        raise NotImplementedError


class OptionalDependencyCheck(PrivacyCheck):
    """
    Base class for checks that require optional dependencies,
    external tools or platform support (nmcli, ufw, exif modules, etc.).

    If the environment does not support the check, `run()` should
    still respond gracefully with a CheckResult (status=INFO) rather
    than raising an exception.
    """

    missing_reason: Optional[str] = None

    def skip(self, reason: str) -> CheckResult:
        """
        Helper method used when a dependency is missing or unsupported.

        Args:
            reason:
                Human-readable reason explaining why the check cannot run.

        Returns:
            A CheckResult with neutral (INFO) status indicating the check
            was skipped.
        """
        from ..core.models import CheckStatus, CheckResult

        logger.info("Skipping privacy check '%s': %s", self.name, reason)
        self.missing_reason = reason

        return CheckResult(
            name=self.name,
            status=CheckStatus.INFO,
            summary=f"{self.name}: skipped ({reason})",
            details={"skipped": True, "reason": reason},
        )
