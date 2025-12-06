"""
IP and basic location leak checking module.

This module queries a GeoIP service to determine the current
public IP address and approximate location. It also inspects
the local IP address and DNS configuration to give a partial
picture of network exposure.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import List, Optional

import requests

from ..core.config import TraceOffConfig
from ..core.logger import get_logger
from ..core.models import LocationInfo, CheckResult, CheckStatus
from ..utils.network import get_default_route_interface

logger = get_logger(__name__)


@dataclass
class IpLeakChecker:
    """
    Perform public IP and basic location checks.

    Attributes:
        config:
            Shared TraceOff configuration instance. The `geoip_endpoint`
            field can be used to override the default GeoIP service.
    """

    config: TraceOffConfig

    # Default GeoIP endpoint – can be overridden by config.geoip_endpoint
    DEFAULT_GEOIP_ENDPOINT = "https://ipinfo.io/json"

    def _geoip_endpoint(self) -> str:
        """
        Determine which GeoIP endpoint to use.

        Returns:
            URL string for GeoIP API endpoint.
        """
        return self.config.geoip_endpoint or self.DEFAULT_GEOIP_ENDPOINT

    def fetch_public_location(self) -> Optional[LocationInfo]:
        """
        Query a GeoIP service to retrieve public IP and approximate location.

        Returns:
            LocationInfo instance if lookup succeeds, None otherwise.
        """
        endpoint = self._geoip_endpoint()
        logger.debug("Querying GeoIP endpoint: %s", endpoint)
        try:
            resp = requests.get(endpoint, timeout=5)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to query GeoIP endpoint: %s", exc)
            return None

        try:
            data = resp.json()
        except ValueError:
            logger.warning("GeoIP endpoint returned non-JSON response.")
            return None

        ip = data.get("ip") or ""
        loc = LocationInfo(
            ip=ip,
            country=data.get("country"),
            region=data.get("region"),
            city=data.get("city"),
            # Some APIs might use 'org' or 'asn'; we keep this flexible.
            asn=str(data.get("asn")) if data.get("asn") else None,
            isp=data.get("org"),
        )
        return loc

    def detect_local_ip(self) -> Optional[str]:
        """
        Attempt to determine the primary local IP address.

        Returns:
            Local IP address as a string, or None if detection fails.
        """
        try:
            # Connect to a public IP without sending data to infer local IP.
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError as exc:
            logger.debug("Failed to detect local IP: %s", exc)
            return None

    def build_location_summary(self) -> str:
        """
        Build a readable summary of current public IP and local network info.

        Returns:
            Multiline string describing public IP, location and local IP.
        """
        loc = self.fetch_public_location()
        local_ip = self.detect_local_ip()
        default_iface = get_default_route_interface()

        lines: List[str] = []
        lines.append("=== TraceOff: Location Summary ===")

        if loc is None:
            lines.append("Public IP: <could not determine>")
        else:
            lines.append(f"Public IP: {loc.ip}")
            lines.append(
                f"Location: {loc.city or '?'} / {loc.region or '?'} / {loc.country or '?'})"
            )
            lines.append(f"ASN/ISP: {loc.asn or loc.isp or '?'}")

        lines.append(f"Local IP: {local_ip or '<unknown>'}")
        lines.append(f"Default route interface: {default_iface or '<unknown>'}")

        return "\n".join(lines)

    def build_check_result(self) -> CheckResult:
        """
        Create a CheckResult representing the IP/GeoIP exposure.

        Returns:
            CheckResult describing the current public IP and location.
        """
        loc = self.fetch_public_location()
        local_ip = self.detect_local_ip()
        default_iface = get_default_route_interface()

        if loc is None:
            summary = "Could not determine public IP or location."
            status = CheckStatus.INFO
            details = {"public_ip": None}
        else:
            summary = f"Public IP {loc.ip} appears in {loc.city or '?'} / {loc.country or '?'}."
            status = CheckStatus.INFO
            details = {
                "public_ip": loc.ip,
                "country": loc.country,
                "region": loc.region,
                "city": loc.city,
                "asn": loc.asn,
                "isp": loc.isp,
            }

        details["local_ip"] = local_ip
        details["default_interface"] = default_iface

        return CheckResult(
            name="ip_leak",
            status=status,
            summary=summary,
            details=details,
        )
