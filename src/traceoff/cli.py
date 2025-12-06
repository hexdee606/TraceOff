"""
Command-line interface (CLI) for TraceOff.

This module defines the root Typer application and its
subcommands. It wires together configuration, logging, and
feature modules such as the MAC manager, privacy checks,
EXIF cleaning, firewall profiles, Wi-Fi and hostname
exposure inspection, auto-fix, plugins, GUI, and more.
"""

from __future__ import annotations

import functools
import sys
from importlib import metadata

import typer

from . import __version__
from .core.config import TraceOffConfig
from .core.logger import configure_logging, get_logger
from .core.exceptions import (
    TraceOffError,
    PrivilegeError,
    CommandExecutionError,
    ConfigError,
)
from .core.plugin_loader import load_plugins
from .modules.mac_manager import MacManager
from .modules.ip_leak_checker import IpLeakChecker
from .modules.dns_leak_checker import DnsLeakChecker
from .modules.ipv6_manager import Ipv6Manager
from .modules.exif_cleaner import ExifCleaner
from .modules.firewall_manager import FirewallManager
from .modules.privacy_report import PrivacyReportBuilder
from .modules.wifi_privacy import WifiPrivacyManager
from .modules.hostname_manager import HostnameManager
from .modules.autofix_manager import AutoFixManager

# Basic metadata
TOOL_NAME = "TraceOff"
TOOL_DESCRIPTION = "Privacy and network-hardening toolkit for security-focused Linux systems."
TOOL_AUTHOR = "Dipen"
TOOL_LICENSE = "MIT License"

# Load configuration and configure logging once at startup.
_config = TraceOffConfig.load_or_default()
configure_logging(_config.log_level)
logger = get_logger(__name__)

# Load plugins (if any) from user plugin directory.
load_plugins()


def handle_errors(func):
    """
    Decorator to provide consistent, user-friendly error handling
    for all CLI commands.

    It catches common TraceOff-specific exceptions and prints
    clear messages and hints instead of raw tracebacks.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PrivilegeError as exc:
            typer.echo("[ERROR] This operation requires elevated privileges.")
            typer.echo(f"Reason: {exc}")
            typer.echo("Hint: Try running this command with 'sudo' on Linux.")
            raise typer.Exit(code=1)
        except CommandExecutionError as exc:
            typer.echo("[ERROR] A required system command failed.")
            typer.echo(f"Reason: {exc}")
            if getattr(exc, "stderr", None):
                typer.echo(f"Command output: {exc.stderr}")
            typer.echo(
                "Hint: Ensure the required tool is installed and available in PATH "
                "(for example: 'ufw', 'ip', 'nmcli', etc.)."
            )
            raise typer.Exit(code=1)
        except ConfigError as exc:
            typer.echo("[ERROR] Configuration error.")
            typer.echo(f"Reason: {exc}")
            typer.echo("Hint: Check or delete your config file at:")
            typer.echo(f"  {_config._config_path()}")  # type: ignore[attr-defined]
            raise typer.Exit(code=1)
        except ValueError as exc:
            typer.echo(f"[ERROR] {exc}")
            raise typer.Exit(code=1)
        except TraceOffError as exc:
            typer.echo(f"[ERROR] {exc}")
            raise typer.Exit(code=1)
        except Exception as exc:
            # Unexpected error – log full details and show a generic hint.
            logger.exception("Unexpected error in CLI command: %s", func.__name__)
            typer.echo("[ERROR] An unexpected error occurred.")
            typer.echo(
                "Hint: Run with environment variable TRACEOFF_LOG_LEVEL=DEBUG "
                "and try again, then check the log output."
            )
            raise typer.Exit(code=1)

    return wrapper


def _get_package_version(package_name: str) -> str:
    """
    Safely get version for a Python package.

    Returns 'not installed' if the package is missing.
    """
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return "not installed"


# Main Typer application instance.
app = typer.Typer(help="TraceOff – privacy and network-hardening toolkit.")

# Sub-apps (namespaces)
mac_app = typer.Typer(help="MAC address spoofing and rotation.")
privacy_app = typer.Typer(help="Privacy and IP/DNS/IPv6 checks and reporting.")
exif_app = typer.Typer(help="File metadata (EXIF) inspection and cleaning.")
firewall_app = typer.Typer(help="Firewall profile management (UFW-based).")
wifi_app = typer.Typer(help="Wi-Fi privacy inspection (NetworkManager-based).")
hostname_app = typer.Typer(help="Hostname and mDNS exposure inspection.")

app.add_typer(mac_app, name="mac")
app.add_typer(privacy_app, name="privacy")
app.add_typer(exif_app, name="exif")
app.add_typer(firewall_app, name="firewall")
app.add_typer(wifi_app, name="wifi")
app.add_typer(hostname_app, name="hostname")


# === Meta / Info commands ==================================================


@app.command("version")
@handle_errors
def show_version() -> None:
    """
    Display TraceOff version and basic metadata.
    """
    python_ver = sys.version.split()[0]
    typer.echo(f"{TOOL_NAME} – {TOOL_DESCRIPTION}")
    typer.echo("")
    typer.echo(f"Version:   {__version__}")
    typer.echo(f"Author:    {TOOL_AUTHOR}")
    typer.echo(f"License:   {TOOL_LICENSE}")
    typer.echo(f"Python:    {python_ver}")


@app.command("about")
@handle_errors
def show_about() -> None:
    """
    Show detailed information about TraceOff, including core
    dependency versions.
    """
    python_ver = sys.version.split()[0]

    typer.echo(f"=== {TOOL_NAME} – About ===")
    typer.echo(TOOL_DESCRIPTION)
    typer.echo("")
    typer.echo(f"Version:   {__version__}")
    typer.echo(f"Author:    {TOOL_AUTHOR}")
    typer.echo(f"License:   {TOOL_LICENSE}")
    typer.echo(f"Python:    {python_ver}")
    typer.echo("")
    typer.echo("Core Python packages:")
    typer.echo(f"  typer:    {_get_package_version('typer')}")
    typer.echo(f"  requests: {_get_package_version('requests')}")
    # Optional dependency – may not be installed
    typer.echo(f"  piexif:   {_get_package_version('piexif')}")
    typer.echo("")
    typer.echo("Config file path:")
    typer.echo(f"  {_config._config_path()}")  # type: ignore[attr-defined]


@app.command("config-path")
@handle_errors
def show_config_path() -> None:
    """
    Display the location of the TraceOff configuration file.
    """
    path = _config._config_path()  # type: ignore[attr-defined]
    typer.echo(str(path))


@app.command("update-check")
@handle_errors
def update_check() -> None:
    """
    Check for newer TraceOff versions via the secure update channel (preview).
    """
    from .core.updater import check_updates

    message = check_updates(__version__)
    typer.echo(message)


@app.command("gui")
@handle_errors
def gui_launch() -> None:
    """
    Launch graphical interface (preview, requires PySide6).
    """
    from .gui.app import gui_entry

    gui_entry()


# === MAC subcommands ======================================================


@mac_app.command("spoof-once")
@handle_errors
def mac_spoof_once(
        iface: str = typer.Option(
            ...,
            "--iface",
            "-i",
            help="Name of the network interface whose MAC should be changed.",
        ),
        vendor_like: bool = typer.Option(
            True,
            "--vendor-like/--fully-random",
            help="Use vendor-like MAC prefixes or fully random locally-administered MACs.",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Show what would be done without applying any changes.",
        ),
) -> None:
    """
    Change the MAC address of a single interface once.
    """
    manager = MacManager(config=_config)
    result = manager.change_mac_once(
        interface=iface,
        vendor_like=vendor_like,
        dry_run=dry_run,
    )
    typer.echo(
        f"Interface: {result.interface}\n"
        f"Old MAC:   {result.old_mac or '<unknown>'}\n"
        f"New MAC:   {result.new_mac}\n"
        f"Dry run:   {result.dry_run}"
    )


@mac_app.command("rotate")
@handle_errors
def mac_rotate(
        iface: str = typer.Option(
            ...,
            "--iface",
            "-i",
            help="Name of the network interface whose MAC should be rotated.",
        ),
        interval: int = typer.Option(
            300,
            "--interval",
            "-t",
            help="Rotation interval in seconds.",
        ),
        vendor_like: bool = typer.Option(
            True,
            "--vendor-like/--fully-random",
            help="Use vendor-like MAC prefixes or fully random locally-administered MACs.",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Simulate rotation without applying changes.",
        ),
) -> None:
    """
    Continuously rotate the MAC address of an interface.
    """
    manager = MacManager(config=_config)
    manager.rotate_mac(
        interface=iface,
        interval_seconds=interval,
        vendor_like=vendor_like,
        dry_run=dry_run,
    )


# === Privacy subcommands ==================================================


@privacy_app.command("location-check")
@handle_errors
def privacy_location_check() -> None:
    """
    Show current public IP, ASN, and approximate geolocation.
    """
    checker = IpLeakChecker(config=_config)
    report = checker.build_location_summary()
    typer.echo(report)


@privacy_app.command("dns-check")
@handle_errors
def privacy_dns_check() -> None:
    """
    Inspect DNS configuration and highlight potential DNS leaks.
    """
    checker = DnsLeakChecker(config=_config)
    summary = checker.build_human_summary()
    typer.echo(summary)


@privacy_app.command("ipv6-status")
@handle_errors
def privacy_ipv6_status() -> None:
    """
    Show current IPv6 status and basic privacy implications.
    """
    mgr = Ipv6Manager(config=_config)
    result = mgr.build_status_check()
    typer.echo("=== TraceOff: IPv6 Status ===")
    typer.echo(result.summary)
    typer.echo(f"Details: {result.details}")


@privacy_app.command("ipv6-disable")
@handle_errors
def privacy_ipv6_disable(
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Show sysctl commands that would be executed without applying changes.",
        )
) -> None:
    """
    Temporarily disable IPv6 system-wide via sysctl.

    Requires root privileges on Linux.
    """
    mgr = Ipv6Manager(config=_config)
    mgr.disable_ipv6(dry_run=dry_run)
    typer.echo("Requested IPv6 disable operation.")


@privacy_app.command("ipv6-enable")
@handle_errors
def privacy_ipv6_enable(
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Show sysctl commands that would be executed without applying changes.",
        )
) -> None:
    """
    Temporarily enable IPv6 system-wide via sysctl.

    Requires root privileges on Linux.
    """
    mgr = Ipv6Manager(config=_config)
    mgr.enable_ipv6(dry_run=dry_run)
    typer.echo("Requested IPv6 enable operation.")


@privacy_app.command("checkup")
@handle_errors
def privacy_checkup(
        output_format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="Output format: 'text' (default) or 'json'.",
        )
) -> None:
    """
    Run a full privacy checkup and print a summary report.

    Use --format json for machine-readable output.
    """
    builder = PrivacyReportBuilder(config=_config)

    fmt = output_format.lower()
    if fmt == "json":
        typer.echo(builder.render_json())
    elif fmt == "text":
        report_text = builder.render_human_readable()
        typer.echo(report_text)
    else:
        typer.echo("Unsupported format. Use 'text' or 'json'.")
        raise typer.Exit(code=1)


@privacy_app.command("autofix")
@handle_errors
def privacy_autofix() -> None:
    """
    Interactively apply recommended privacy fixes (preview).

    This may change system settings such as:
    - MAC address
    - IPv6 enable/disable
    - Firewall profile (UFW)
    """
    manager = AutoFixManager(_config)
    manager.run_interactive()


# === EXIF subcommands =====================================================


@exif_app.command("scan")
@handle_errors
def exif_scan(
        path: str = typer.Argument(..., help="File or directory path to scan."),
        recursive: bool = typer.Option(
            True,
            "--recursive/--no-recursive",
            help="Recurse into subdirectories when scanning.",
        ),
) -> None:
    """
    Scan for image files that may contain EXIF metadata.
    """
    cleaner = ExifCleaner(config=_config)
    summary = cleaner.scan(path=path, recursive=recursive)
    typer.echo(summary)


@exif_app.command("clean")
@handle_errors
def exif_clean(
        path: str = typer.Argument(..., help="File or directory path to clean."),
        recursive: bool = typer.Option(
            True,
            "--recursive/--no-recursive",
            help="Recurse into subdirectories when cleaning.",
        ),
        backup: bool = typer.Option(
            True,
            "--backup/--no-backup",
            help="Create backup files before modifying images.",
        ),
) -> None:
    """
    Remove EXIF metadata from supported image files.
    """
    cleaner = ExifCleaner(config=_config)
    summary = cleaner.clean(path=path, recursive=recursive, backup=backup)
    typer.echo(summary)


# === Firewall subcommands =================================================


@firewall_app.command("set")
@handle_errors
def firewall_set(
        profile: str = typer.Argument(
            ...,
            help="Firewall profile name (e.g. 'public', 'home').",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Show UFW commands that would be run without applying them.",
        ),
) -> None:
    """
    Apply a firewall profile using UFW (Linux only).

    Requires root privileges.
    """
    manager = FirewallManager(config=_config)
    manager.apply_profile(profile_name=profile, dry_run=dry_run)
    typer.echo(f"Requested firewall profile '{profile}' apply operation.")


@firewall_app.command("status")
@handle_errors
def firewall_status() -> None:
    """
    Display firewall status using UFW.
    """
    manager = FirewallManager(config=_config)
    status_text = manager.get_status()
    typer.echo(status_text)


# === Wi-Fi subcommands ====================================================


@wifi_app.command("list-known")
@handle_errors
def wifi_list_known() -> None:
    """
    List known Wi-Fi networks and their auto-connect status.

    Requires NetworkManager (nmcli). On systems without nmcli,
    a short message will be shown instead.
    """
    mgr = WifiPrivacyManager(config=_config)
    summary = mgr.build_human_summary()
    typer.echo(summary)


# === Hostname subcommands =================================================


@hostname_app.command("report")
@handle_errors
def hostname_report() -> None:
    """
    Show hostname and mDNS (Avahi) exposure summary.
    """
    mgr = HostnameManager(config=_config)
    summary = mgr.build_human_summary()
    typer.echo(summary)


# === Root callback ========================================================


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """
    Base command for TraceOff.

    If no subcommand is provided, show help.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
