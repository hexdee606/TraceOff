"""
MAC address management module.

This module implements high-level operations to spoof or rotate
MAC addresses on network interfaces using an object-oriented
approach. It is responsible for:

* Validating interface existence
* Generating realistic or fully random MAC addresses
* Applying MAC changes (with dry-run support)
* Optionally rotating MAC addresses at fixed intervals
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..core.config import TraceOffConfig
from ..core.exceptions import PrivilegeError
from ..core.logger import get_logger
from ..core.models import MacChangeResult
from ..utils.network import list_network_interfaces
from ..utils.shell import run_command

logger = get_logger(__name__)


@dataclass
class MacManager:
    """
    Manage MAC spoofing operations for network interfaces.

    This class serves as a high-level façade around the low-level
    command execution required to change MAC addresses. All logic
    related to choosing a new MAC, validating interfaces and
    performing rotations lives here.

    Attributes:
        config:
            Shared TraceOff configuration instance. At the moment,
            this is mostly used for defaults, but future versions
            may include per-interface profiles, rotation settings, etc.
    """

    config: TraceOffConfig

    # Small set of example vendor prefixes (OUIs). In a real-world
    # version this list can be expanded or sourced from an external
    # file. These values are only for making vendor-like MACs, not
    # for strict vendor emulation.
    VENDOR_PREFIXES: List[str] = field(default_factory=lambda: [
        "00:16:3e",
        "00:1A:2B",
        "00:25:9C",
    ])

    @staticmethod
    def _require_root() -> None:
        """
        Ensure that the current process is running with root privileges.

        Many network operations, including MAC changes, require root.
        This method raises PrivilegeError if the effective user ID is
        not zero.

        Raises:
            PrivilegeError:
                If the effective user ID is not root.
        """
        if os.geteuid() != 0:
            raise PrivilegeError(
                "MAC operations require root privileges. "
                "Please run this command with sudo or as root."
            )

    @staticmethod
    def _interface_exists(interface: str) -> bool:
        """
        Check whether the given network interface exists.

        Args:
            interface:
                Name of the network interface to check.

        Returns:
            True if the interface exists, False otherwise.
        """
        return interface in list_network_interfaces()

    @staticmethod
    def _read_current_mac(interface: str) -> Optional[str]:
        """
        Read the current MAC address of an interface, if possible.

        Args:
            interface:
                Name of the network interface.

        Returns:
            The current MAC address string, or None if it cannot
            be determined.
        """
        address_path = Path("/sys/class/net") / interface / "address"
        try:
            return address_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            logger.debug("MAC address file not found for interface %s", interface)
        except OSError as exc:
            logger.debug("Failed to read MAC for %s: %s", interface, exc)
        return None

    @staticmethod
    def _is_interface_up(interface: str) -> bool:
        """
        Determine whether the given interface is currently up.

        Args:
            interface:
                Name of the network interface.

        Returns:
            True if the interface is up, False otherwise.
        """
        operstate_path = Path("/sys/class/net") / interface / "operstate"
        try:
            state = operstate_path.read_text(encoding="utf-8").strip()
            return state == "up"
        except FileNotFoundError:
            logger.debug("operstate file not found for interface %s", interface)
        except OSError as exc:
            logger.debug("Failed to read operstate for %s: %s", interface, exc)
        return False

    def _generate_mac(self, vendor_like: bool = True) -> str:
        """
        Generate a random MAC address.

        Args:
            vendor_like:
                If True, use a realistic vendor prefix from VENDOR_PREFIXES
                and randomize the remaining bytes. If False, generate a
                fully random locally-administered, unicast MAC address.

        Returns:
            A MAC address string in the form 'aa:bb:cc:dd:ee:ff'.
        """
        if vendor_like and self.VENDOR_PREFIXES:
            prefix = random.choice(self.VENDOR_PREFIXES)
            suffix = ":".join(f"{random.randint(0, 255):02x}" for _ in range(3))
            mac = f"{prefix}:{suffix}"
            logger.debug("Generated vendor-like MAC: %s", mac)
            return mac

        # Construct a locally-administered unicast MAC:
        #  - Set the "locally administered" bit (bit 1) of the first octet.
        #  - Ensure the "multicast" bit (bit 0) is not set.
        first_octet = random.randint(0, 255)
        first_octet = (first_octet | 0b00000010) & 0b11111110
        rest = [random.randint(0, 255) for _ in range(5)]
        octets = [first_octet] + rest
        mac = ":".join(f"{octet:02x}" for octet in octets)
        logger.debug("Generated fully random MAC: %s", mac)
        return mac

    def change_mac_once(
            self,
            interface: str,
            vendor_like: bool = True,
            dry_run: bool = False,
    ) -> MacChangeResult:
        """
        Change MAC address of a specific interface once.

        This method performs several steps:
        * Validates that the interface exists.
        * Ensures root privileges are present.
        * Reads the current MAC (if possible).
        * Generates a new MAC address.
        * Brings the interface down, sets the new MAC, and restores
          its previous up/down state.

        Args:
            interface:
                Name of the network interface to modify.
            vendor_like:
                If True, generate vendor-like MACs using VENDOR_PREFIXES.
                If False, generate fully random locally-administered MACs.
            dry_run:
                If True, no actual changes are applied; the commands
                are logged but not executed.

        Returns:
            MacChangeResult describing the change that was applied
            (or simulated if dry_run=True).

        Raises:
            PrivilegeError:
                If the operation is attempted without root privileges.
            TraceOffError:
                If interface does not exist or commands fail. (Command
                failures are wrapped in CommandExecutionError.)
        """
        self._require_root()

        if not self._interface_exists(interface):
            raise ValueError(f"Interface '{interface}' does not exist.")

        old_mac = self._read_current_mac(interface)
        was_up = self._is_interface_up(interface)
        new_mac = self._generate_mac(vendor_like=vendor_like)

        logger.info(
            "Changing MAC on %s from %s to %s (dry_run=%s)",
            interface,
            old_mac or "<unknown>",
            new_mac,
            dry_run,
        )

        # Bring interface down before changing MAC.
        run_command(["ip", "link", "set", "dev", interface, "down"], dry_run=dry_run)
        # Assign new MAC address.
        run_command(
            ["ip", "link", "set", "dev", interface, "address", new_mac],
            dry_run=dry_run,
        )
        # Restore original up/down state.
        if was_up:
            run_command(["ip", "link", "set", "dev", interface, "up"], dry_run=dry_run)

        return MacChangeResult(
            interface=interface,
            old_mac=old_mac,
            new_mac=new_mac,
            dry_run=dry_run,
        )

    def rotate_mac(
            self,
            interface: str,
            interval_seconds: int = 300,
            vendor_like: bool = True,
            dry_run: bool = False,
    ) -> None:
        """
        Continuously rotate MAC address on an interface.

        This method enters a loop that repeatedly calls
        `change_mac_once` and then sleeps for the specified
        interval. It is intended for use in long-running
        privacy sessions. Press Ctrl+C to stop.

        Args:
            interface:
                Name of the network interface to rotate.
            interval_seconds:
                Time between rotations in seconds.
            vendor_like:
                If True, generate vendor-like MACs.
            dry_run:
                If True, do not apply changes; only log actions.

        Raises:
            PrivilegeError:
                If not run as root.

        Notes:
            This method runs until interrupted by KeyboardInterrupt.
        """
        self._require_root()

        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero.")

        logger.info(
            "Starting MAC rotation on %s every %d seconds "
            "(vendor_like=%s, dry_run=%s)",
            interface,
            interval_seconds,
            vendor_like,
            dry_run,
        )

        try:
            while True:
                self.change_mac_once(
                    interface=interface,
                    vendor_like=vendor_like,
                    dry_run=dry_run,
                )
                if dry_run:
                    # In dry-run mode, we still sleep to simulate behaviour.
                    logger.info("Dry run: waiting %d seconds before next rotation...", interval_seconds)
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("MAC rotation on %s interrupted by user.", interface)
