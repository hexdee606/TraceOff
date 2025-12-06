"""
Registry and execution coordinator for privacy checks.

This module enables TraceOff to discover, register and execute
privacy checks in a predictable sequence. This helps support
features such as:

- selective check execution
- full system audit
- JSON export mode
- auto-fix workflows (future)
"""

from __future__ import annotations

from typing import Dict, List, Type

from .base import PrivacyCheck
from ..core.logger import get_logger
from ..core.models import PrivacyReport, CheckResult, CheckStatus

logger = get_logger(__name__)


class CheckRegistry:
    """
    Registry for available privacy checks.

    This class stores mappings from check names to check classes.
    It allows dynamic listing, enabling/disabling, and running of
    checks individually or in bulk.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[PrivacyCheck]] = {}

    def register(self, check_cls: Type[PrivacyCheck]) -> None:
        """
        Register a privacy check class.

        Args:
            check_cls:
                A subclass of PrivacyCheck.

        Raises:
            ValueError:
                If a check with the same name is already registered.
        """
        name = getattr(check_cls, "name", check_cls.__name__)
        if name in self._registry:
            raise ValueError(f"Privacy check '{name}' already registered.")

        logger.debug("Registering privacy check: %s", name)
        self._registry[name] = check_cls

    def list_checks(self) -> List[str]:
        """
        List registered privacy check names.

        Returns:
            List of check identifiers.
        """
        return sorted(self._registry.keys())

    def run_all(self) -> PrivacyReport:
        """
        Execute all registered privacy checks and return a PrivacyReport.

        Returns:
            A PrivacyReport instance containing check results.
        """
        report = PrivacyReport()

        for name, check_cls in self._registry.items():
            logger.info("Running check: %s", name)
            try:
                instance = check_cls()
                result = instance.run()
                report.add_result(result)
            except Exception as exc:
                logger.error("Privacy check '%s' failed: %s", name, exc)
                # If a check fails unexpectedly, treat it as a WARNING instead of crashing.
                report.add_result(
                    CheckResult(
                        name=name,
                        status=CheckStatus.WARNING,
                        summary="Check failed unexpectedly.",
                        details={"error": str(exc)},
                    )
                )

        return report


# Global shared instance
registry = CheckRegistry()
