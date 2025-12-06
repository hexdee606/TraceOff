"""
Network-related helper functions.

This module provides basic discovery helpers such as listing
network interfaces or determining the default route. Higher-
level modules (e.g. MAC manager, leak checkers) build on top
of these primitives.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from .shell import run_command
from ..core.logger import get_logger

logger = get_logger(__name__)


def list_network_interfaces() -> List[str]:
    """
    List available network interfaces, excluding the loopback interface.

    This function inspects `/sys/class/net` and returns a list of
    interface names. The result does not include 'lo'.

    Returns:
        A list of interface names. The list may be empty if the system
        does not expose `/sys/class/net` or in constrained environments.
    """
    interfaces: List[str] = []
    net_path = Path("/sys/class/net")
    if not net_path.exists():
        logger.debug("/sys/class/net does not exist; no interfaces listed.")
        return interfaces

    for entry in net_path.iterdir():
        if not entry.is_dir():
            continue
        if entry.name == "lo":
            continue
        interfaces.append(entry.name)

    logger.debug("Detected network interfaces: %s", interfaces)
    return interfaces


def get_default_route_interface() -> Optional[str]:
    """
    Determine the network interface used for the default route.

    This function parses the output of `ip route show default` and
    attempts to extract the name of the interface carrying the default
    route. It is useful for guessing which interface represents the
    main outbound connection (e.g. Wi-Fi vs VPN).

    Returns:
        Name of the default route interface, or None if it cannot be
        determined.
    """
    try:
        proc = run_command(["ip", "route", "show", "default"], check=False)
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if "dev" in parts:
                idx = parts.index("dev")
                if idx + 1 < len(parts):
                    iface = parts[idx + 1]
                    logger.debug("Default route interface detected: %s", iface)
                    return iface
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Failed to detect default route interface: %s", exc)

    logger.debug("No default route interface detected.")
    return None


def detect_vpn_like_interfaces() -> List[str]:
    """
    Attempt to detect network interfaces that look like VPN tunnels.

    This is a heuristic that considers common naming patterns such
    as 'tun0', 'tun1', 'wg0', 'ppp0', etc. It does not guarantee that
    a VPN is active, but can provide a useful hint for privacy checks.

    Returns:
        List of interface names that appear to be VPN-like.
    """
    candidates = {"tun", "wg", "ppp"}
    interfaces = list_network_interfaces()
    vpn_like: List[str] = []

    for iface in interfaces:
        for prefix in candidates:
            if iface.startswith(prefix):
                vpn_like.append(iface)
                break

    logger.debug("VPN-like interfaces detected: %s", vpn_like)
    return vpn_like
