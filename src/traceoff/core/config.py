"""
Configuration management for TraceOff.

This module defines the configuration model and helpers
for loading and saving configuration from a user-specific
location such as the XDG config directory.

All modules that need user-tunable settings should depend
on TraceOffConfig instead of hard-coding constants.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class TraceOffConfig:
    """
    Data class representing TraceOff configuration.

    Attributes:
        geoip_endpoint: Optional URL of a GeoIP HTTP API endpoint.
        default_interface: Optional default network interface for MAC operations.
        log_level: Logging verbosity (e.g. 'INFO', 'DEBUG', 'WARNING').
    """

    geoip_endpoint: Optional[str] = None
    default_interface: Optional[str] = None
    log_level: str = "INFO"

    # Internal constants for config storage
    CONFIG_DIR_NAME = "traceoff"
    CONFIG_FILE_NAME = "config.json"

    @classmethod
    def _config_path(cls) -> Path:
        """
        Compute the configuration file path for the current user.

        Returns:
            Path to the configuration file.
        """
        xdg_config = Path.home() / ".config"
        config_dir = xdg_config / cls.CONFIG_DIR_NAME
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / cls.CONFIG_FILE_NAME

    @classmethod
    def load_or_default(cls) -> "TraceOffConfig":
        """
        Load configuration from disk or return a default instance.

        If the configuration file is missing or cannot be parsed,
        a new TraceOffConfig with default values is returned.

        Returns:
            Loaded TraceOffConfig instance or a default configuration.
        """
        path = cls._config_path()
        if not path.exists():
            return cls()
        try:
            with path.open("r", encoding="utf-8") as fh:
                data: Dict[str, Any] = json.load(fh)
            return cls(**data)
        except Exception:
            # Fall back to default configuration on any error.
            return cls()

    def save(self) -> None:
        """
        Persist the current configuration to disk.

        The configuration is saved in JSON format under the
        user's XDG configuration directory.
        """
        path = self._config_path()
        with path.open("w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=2)
