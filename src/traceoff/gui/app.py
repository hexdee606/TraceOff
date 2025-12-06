"""
Graphical user interface for TraceOff (PySide6).

This GUI provides a tabbed interface over the main TraceOff features:

- Privacy checkup (text + JSON)
- MAC spoofing (single change)
- EXIF scan & clean
- Firewall, DNS and IPv6 inspection
- Wi-Fi & hostname exposure inspection
- About & update check

Error handling:
    All actions are wrapped with structured exception handling and
    show user-friendly error dialogs with contextual hints instead
    of raw tracebacks.
"""

from __future__ import annotations

import json
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from .. import __version__
from ..core.config import TraceOffConfig
from ..core.exceptions import (
    TraceOffError,
    PrivilegeError,
    CommandExecutionError,
    ConfigError,
)
from ..core.logger import get_logger
from ..core.updater import check_updates
from ..modules.privacy_report import PrivacyReportBuilder
from ..modules.mac_manager import MacManager
from ..modules.exif_cleaner import ExifCleaner
from ..modules.firewall_manager import FirewallManager
from ..modules.wifi_privacy import WifiPrivacyManager
from ..modules.hostname_manager import HostnameManager
from ..modules.ip_leak_checker import IpLeakChecker
from ..modules.dns_leak_checker import DnsLeakChecker
from ..modules.ipv6_manager import Ipv6Manager

logger = get_logger(__name__)


class TraceOffMainWindow(QMainWindow):
    """
    Main Qt window for the TraceOff GUI.

    All user-triggered actions are wrapped in `try/except` and
    delegated to `_handle_exception` to ensure the user always
    receives clear feedback on what went wrong and what to do next.
    """

    def __init__(self, config: Optional[TraceOffConfig] = None) -> None:
        super().__init__()

        # Safe config loading with error reporting
        if config is not None:
            self.config = config
        else:
            try:
                self.config = TraceOffConfig.load_or_default()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to load TraceOff configuration in GUI: %s", exc)
                # Fallback: attempt a bare config instance
                self.config = TraceOffConfig()
                # We can show a warning once the window exists
                QMessageBox.warning(
                    self,
                    "Configuration Warning",
                    "Failed to load the TraceOff configuration file.\n\n"
                    "A temporary default configuration will be used for this session.\n"
                    "Please check or remove your config file.",
                )

        self.setWindowTitle(f"TraceOff GUI – v{__version__}")
        self.resize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout()
        central.setLayout(root_layout)

        header = QLabel("<h2>TraceOff – Privacy & Network Hardening</h2>")
        header.setTextFormat(Qt.RichText)
        root_layout.addWidget(header)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs, stretch=1)

        # Tabs
        self._init_privacy_tab()
        self._init_mac_tab()
        self._init_exif_tab()
        self._init_network_tab()
        self._init_system_tab()

        # Simple status bar for quick feedback
        self.statusBar().showMessage("Ready")

    # ==== Error handling helpers ==========================================

    def _show_error(self, title: str, message: str, details: Optional[str] = None) -> None:
        """
        Show an error dialog with optional technical details.
        """
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle(title)
        dlg.setText(message)
        if details:
            dlg.setDetailedText(details)
        dlg.exec()

    def _set_status(self, text: str) -> None:
        """
        Update the status bar with a short message.
        """
        self.statusBar().showMessage(text, 8000)  # message stays ~8 seconds

    def _handle_exception(self, exc: Exception, context: str) -> None:
        """
        Map internal exceptions to user-friendly dialogs with hints.

        Args:
            exc:
                The exception instance.
            context:
                Short description of where the error happened (for display).
        """
        # Privilege errors – user needs sudo / root.
        if isinstance(exc, PrivilegeError):
            msg = (
                "This action requires elevated privileges (root).\n\n"
                f"Context: {context}\n\n"
                "Hint:\n"
                "  • Run the equivalent command from a terminal with 'sudo', or\n"
                "  • Start a privileged session depending on your OS."
            )
            self._show_error("Privilege Error", msg, details=str(exc))
            self._set_status("Privilege error: action requires elevated permissions.")
            return

        # Command execution errors – missing system tools, bad exit code.
        if isinstance(exc, CommandExecutionError):
            stderr = getattr(exc, "stderr", "") or ""
            hint_lines = [
                "Hint:",
                "  • Ensure the required tool is installed and available in PATH.",
                "  • Common tools: 'ufw', 'ip', 'nmcli', 'sysctl', etc.",
                "  • Try the same command from a terminal to see behavior.",
            ]

            # Simple heuristic hints based on stderr content:
            lower = stderr.lower()
            if "command not found" in lower or "not recognized" in lower:
                hint_lines.append("  • It looks like a command is missing on this system.")
            if "permission denied" in lower:
                hint_lines.append("  • It looks like this command needs root privileges.")

            msg = (
                    "A required system command failed.\n\n"
                    f"Context: {context}\n\n"
                    + "\n".join(hint_lines)
            )
            self._show_error("Command Failed", msg, details=f"{exc}\n\nstderr:\n{stderr}")
            self._set_status("A system command failed. See error dialog.")
            return

        # Config issues – likely bad JSON or unreadable config file.
        if isinstance(exc, ConfigError):
            cfg_path = getattr(self.config, "_config_path", lambda: "<unknown>")()
            msg = (
                "There is a problem with your TraceOff configuration.\n\n"
                f"Context: {context}\n"
                f"Config file: {cfg_path}\n\n"
                "Hint:\n"
                "  • Check that the JSON is valid.\n"
                "  • If unsure, temporarily delete or rename the config file."
            )
            self._show_error("Configuration Error", msg, details=str(exc))
            self._set_status("Configuration error. Please check your config file.")
            return

        # Generic TraceOffError – something we raised on purpose.
        if isinstance(exc, TraceOffError):
            msg = (
                f"A TraceOff error occurred.\n\nContext: {context}\n\n"
                "Hint:\n"
                "  • Check the detailed information for more context.\n"
                "  • If this persists, consider opening a bug report."
            )
            self._show_error("TraceOff Error", msg, details=str(exc))
            self._set_status("TraceOff error. See error dialog for details.")
            return

        # Anything else – unexpected
        logger.exception("Unhandled exception in GUI (%s): %s", context, exc)
        msg = (
            "An unexpected error occurred inside the GUI.\n\n"
            f"Context: {context}\n\n"
            "Hint:\n"
            "  • Try running the equivalent CLI command for more detail.\n"
            "  • Run with TRACEOFF_LOG_LEVEL=DEBUG to collect logs.\n"
            "  • If reproducible, consider filing an issue on GitHub."
        )
        self._show_error("Unexpected Error", msg, details=repr(exc))
        self._set_status("Unexpected error. See error dialog and logs for details.")

    # ==== Privacy tab =====================================================

    def _init_privacy_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        btn_row = QHBoxLayout()

        btn_check_text = QPushButton("Run Full Checkup (Text)")
        btn_check_text.clicked.connect(self._privacy_run_check_text)
        btn_row.addWidget(btn_check_text)

        btn_check_json = QPushButton("Run Full Checkup (JSON)")
        btn_check_json.clicked.connect(self._privacy_run_check_json)
        btn_row.addWidget(btn_check_json)

        btn_ip = QPushButton("Quick: Public IP & Location")
        btn_ip.clicked.connect(self._privacy_show_ip)
        btn_row.addWidget(btn_ip)

        layout.addLayout(btn_row)

        self.privacy_output = QTextEdit()
        self.privacy_output.setReadOnly(True)
        layout.addWidget(self.privacy_output, stretch=1)

        self.tabs.addTab(tab, "Privacy Checkup")

    def _privacy_run_check_text(self) -> None:
        """
        Run full privacy checkup and show human-readable output.
        """
        self._set_status("Running privacy checkup (text)…")
        try:
            builder = PrivacyReportBuilder(config=self.config)
            text = builder.render_human_readable()
            self.privacy_output.setPlainText(text)
            self._set_status("Privacy checkup complete.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Running privacy checkup (text)")

    def _privacy_run_check_json(self) -> None:
        """
        Run full privacy checkup and show JSON output.
        """
        self._set_status("Running privacy checkup (JSON)…")
        try:
            builder = PrivacyReportBuilder(config=self.config)
            text = builder.render_json(indent=2)
            parsed = json.loads(text)
            pretty = json.dumps(parsed, indent=2)
            self.privacy_output.setPlainText(pretty)
            self._set_status("Privacy checkup (JSON) complete.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Running privacy checkup (JSON)")

    def _privacy_show_ip(self) -> None:
        """
        Show quick IP + location summary.
        """
        self._set_status("Fetching public IP and geolocation…")
        try:
            checker = IpLeakChecker(config=self.config)
            summary = checker.build_location_summary()
            self.privacy_output.setPlainText(summary)
            self._set_status("Public IP check complete.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Fetching public IP & location")

    # ==== MAC tab =========================================================

    def _init_mac_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        form = QFormLayout()

        self.mac_iface_input = QLineEdit()
        if getattr(self.config, "default_interface", None):
            self.mac_iface_input.setText(self.config.default_interface)  # type: ignore[attr-defined]
        form.addRow("Interface:", self.mac_iface_input)

        self.mac_vendor_like = QCheckBox("Use vendor-like MAC prefixes")
        self.mac_vendor_like.setChecked(True)
        form.addRow("", self.mac_vendor_like)

        self.mac_dry_run = QCheckBox("Dry run (do not apply changes)")
        self.mac_dry_run.setChecked(False)
        form.addRow("", self.mac_dry_run)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_spoof = QPushButton("Spoof MAC Once")
        btn_spoof.clicked.connect(self._mac_spoof_once)
        btn_row.addWidget(btn_spoof)

        layout.addLayout(btn_row)

        self.mac_output = QTextEdit()
        self.mac_output.setReadOnly(True)
        layout.addWidget(self.mac_output, stretch=1)

        self.tabs.addTab(tab, "MAC Tools")

    def _mac_spoof_once(self) -> None:
        """
        Perform a one-time MAC spoofing operation.
        """
        iface = self.mac_iface_input.text().strip()
        if not iface:
            self._show_error(
                "Input Error",
                "Please specify a network interface (for example: 'wlan0').",
            )
            self._set_status("MAC spoof aborted: no interface specified.")
            return

        self._set_status(f"Spoofing MAC on interface '{iface}'…")
        try:
            manager = MacManager(config=self.config)
            result = manager.change_mac_once(
                interface=iface,
                vendor_like=self.mac_vendor_like.isChecked(),
                dry_run=self.mac_dry_run.isChecked(),
            )
            self.mac_output.setPlainText(
                f"Interface: {result.interface}\n"
                f"Old MAC:   {result.old_mac or '<unknown>'}\n"
                f"New MAC:   {result.new_mac}\n"
                f"Dry run:   {result.dry_run}"
            )
            self._set_status("MAC spoof operation completed.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "MAC spoof once")

    # ==== EXIF tab ========================================================

    def _init_exif_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        path_row = QHBoxLayout()
        self.exif_path_input = QLineEdit()
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._exif_browse)

        path_row.addWidget(QLabel("Path:"))
        path_row.addWidget(self.exif_path_input, stretch=1)
        path_row.addWidget(btn_browse)

        layout.addLayout(path_row)

        options_row = QHBoxLayout()
        self.exif_recursive = QCheckBox("Recursive")
        self.exif_recursive.setChecked(True)
        options_row.addWidget(self.exif_recursive)

        self.exif_backup = QCheckBox("Backup before cleaning")
        self.exif_backup.setChecked(True)
        options_row.addWidget(self.exif_backup)

        layout.addLayout(options_row)

        btn_row = QHBoxLayout()
        btn_scan = QPushButton("Scan for EXIF")
        btn_scan.clicked.connect(self._exif_scan)
        btn_row.addWidget(btn_scan)

        btn_clean = QPushButton("Clean EXIF")
        btn_clean.clicked.connect(self._exif_clean)
        btn_row.addWidget(btn_clean)

        layout.addLayout(btn_row)

        self.exif_output = QTextEdit()
        self.exif_output.setReadOnly(True)
        layout.addWidget(self.exif_output, stretch=1)

        self.tabs.addTab(tab, "EXIF Tools")

    def _exif_browse(self) -> None:
        """
        Open a directory selection dialog for EXIF operations.
        """
        path = QFileDialog.getExistingDirectory(self, "Select directory")
        if path:
            self.exif_path_input.setText(path)

    def _exif_scan(self) -> None:
        path = self.exif_path_input.text().strip()
        if not path:
            self._show_error("Input Error", "Please select a file or directory to scan.")
            self._set_status("EXIF scan aborted: no path selected.")
            return
        self._set_status(f"Scanning for EXIF metadata in: {path}")
        try:
            cleaner = ExifCleaner(config=self.config)
            summary = cleaner.scan(path=path, recursive=self.exif_recursive.isChecked())
            self.exif_output.setPlainText(summary)
            self._set_status("EXIF scan completed.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "EXIF scan")

    def _exif_clean(self) -> None:
        path = self.exif_path_input.text().strip()
        if not path:
            self._show_error("Input Error", "Please select a file or directory to clean.")
            self._set_status("EXIF clean aborted: no path selected.")
            return
        self._set_status(f"Cleaning EXIF metadata in: {path}")
        try:
            cleaner = ExifCleaner(config=self.config)
            summary = cleaner.clean(
                path=path,
                recursive=self.exif_recursive.isChecked(),
                backup=self.exif_backup.isChecked(),
            )
            self.exif_output.setPlainText(summary)
            self._set_status("EXIF clean operation completed.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "EXIF clean")

    # ==== Network / Firewall / DNS / IPv6 tab =============================

    def _init_network_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Firewall controls
        fw_group = QVBoxLayout()
        fw_group.addWidget(QLabel("<b>Firewall (UFW)</b>"))

        fw_btn_row = QHBoxLayout()
        btn_fw_status = QPushButton("Show Firewall Status")
        btn_fw_status.clicked.connect(self._fw_show_status)
        fw_btn_row.addWidget(btn_fw_status)

        self.fw_dry_run = QCheckBox("Dry run when applying profiles")
        self.fw_dry_run.setChecked(True)
        fw_btn_row.addWidget(self.fw_dry_run)

        fw_group.addLayout(fw_btn_row)

        profile_row = QHBoxLayout()
        btn_fw_public = QPushButton("Apply 'public' profile")
        btn_fw_public.clicked.connect(lambda: self._fw_apply_profile("public"))
        profile_row.addWidget(btn_fw_public)

        btn_fw_home = QPushButton("Apply 'home' profile")
        btn_fw_home.clicked.connect(lambda: self._fw_apply_profile("home"))
        profile_row.addWidget(btn_fw_home)

        fw_group.addLayout(profile_row)

        layout.addLayout(fw_group)

        # DNS / IPv6 buttons
        dns_ipv6_row = QHBoxLayout()
        btn_dns = QPushButton("DNS Check")
        btn_dns.clicked.connect(self._dns_check)
        dns_ipv6_row.addWidget(btn_dns)

        btn_ipv6_status = QPushButton("IPv6 Status")
        btn_ipv6_status.clicked.connect(self._ipv6_status)
        dns_ipv6_row.addWidget(btn_ipv6_status)

        btn_ipv6_disable = QPushButton("Disable IPv6 (dry-run)")
        btn_ipv6_disable.clicked.connect(lambda: self._ipv6_toggle(disable=True))
        dns_ipv6_row.addWidget(btn_ipv6_disable)

        btn_ipv6_enable = QPushButton("Enable IPv6 (dry-run)")
        btn_ipv6_enable.clicked.connect(lambda: self._ipv6_toggle(disable=False))
        dns_ipv6_row.addWidget(btn_ipv6_enable)

        layout.addLayout(dns_ipv6_row)

        self.network_output = QTextEdit()
        self.network_output.setReadOnly(True)
        layout.addWidget(self.network_output, stretch=1)

        self.tabs.addTab(tab, "Network & Firewall")

    def _fw_show_status(self) -> None:
        self._set_status("Querying firewall status (UFW)…")
        try:
            manager = FirewallManager(config=self.config)
            status = manager.get_status()
            self.network_output.setPlainText(status)
            self._set_status("Firewall status retrieved.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Firewall status")

    def _fw_apply_profile(self, profile: str) -> None:
        dry_run = self.fw_dry_run.isChecked()
        self._set_status(f"Applying firewall profile '{profile}' (dry_run={dry_run})…")
        try:
            manager = FirewallManager(config=self.config)
            manager.apply_profile(profile_name=profile, dry_run=dry_run)
            text = f"Requested firewall profile '{profile}' apply (dry_run={dry_run})."
            self.network_output.append(text)
            self._set_status(f"Firewall profile '{profile}' apply requested.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, f"Apply firewall profile '{profile}'")

    def _dns_check(self) -> None:
        self._set_status("Running DNS leak check…")
        try:
            checker = DnsLeakChecker(config=self.config)
            summary = checker.build_human_summary()
            self.network_output.setPlainText(summary)
            self._set_status("DNS check completed.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "DNS leak check")

    def _ipv6_status(self) -> None:
        self._set_status("Checking IPv6 status…")
        try:
            mgr = Ipv6Manager(config=self.config)
            result = mgr.build_status_check()
            self.network_output.setPlainText(
                "=== IPv6 Status ===\n"
                f"{result.summary}\n\n"
                f"Details: {result.details}"
            )
            self._set_status("IPv6 status retrieved.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "IPv6 status")

    def _ipv6_toggle(self, disable: bool) -> None:
        """
        IPv6 enable/disable via sysctl in 'dry-run' mode from the GUI
        to avoid surprising the user. For real changes, prefer the CLI.
        """
        action = "disable" if disable else "enable"
        self._set_status(f"Requesting IPv6 {action} (dry-run only)…")
        try:
            mgr = Ipv6Manager(config=self.config)
            if disable:
                mgr.disable_ipv6(dry_run=True)
                msg = (
                    "Requested IPv6 disable (dry-run only).\n"
                    "For real changes, use the CLI with appropriate privileges."
                )
            else:
                mgr.enable_ipv6(dry_run=True)
                msg = (
                    "Requested IPv6 enable (dry-run only).\n"
                    "For real changes, use the CLI with appropriate privileges."
                )
            self.network_output.append(msg)
            self._set_status(f"IPv6 {action} dry-run completed.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, f"IPv6 {action} (dry-run)")

    # ==== System / Wi-Fi / Hostname / Updates tab =========================

    def _init_system_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        btn_row1 = QHBoxLayout()
        btn_wifi = QPushButton("Wi-Fi Privacy Summary")
        btn_wifi.clicked.connect(self._wifi_summary)
        btn_row1.addWidget(btn_wifi)

        btn_hostname = QPushButton("Hostname Exposure Summary")
        btn_hostname.clicked.connect(self._hostname_summary)
        btn_row1.addWidget(btn_hostname)

        layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        btn_about = QPushButton("About TraceOff")
        btn_about.clicked.connect(self._about_dialog)
        btn_row2.addWidget(btn_about)

        btn_update = QPushButton("Check for Updates")
        btn_update.clicked.connect(self._update_check)
        btn_row2.addWidget(btn_update)

        layout.addLayout(btn_row2)

        self.system_output = QTextEdit()
        self.system_output.setReadOnly(True)
        layout.addWidget(self.system_output, stretch=1)

        self.tabs.addTab(tab, "System & Info")

    def _wifi_summary(self) -> None:
        self._set_status("Building Wi-Fi privacy summary…")
        try:
            mgr = WifiPrivacyManager(config=self.config)
            summary = mgr.build_human_summary()
            self.system_output.setPlainText(summary)
            self._set_status("Wi-Fi privacy summary updated.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Wi-Fi privacy summary")

    def _hostname_summary(self) -> None:
        self._set_status("Checking hostname and mDNS exposure…")
        try:
            mgr = HostnameManager(config=self.config)
            summary = mgr.build_human_summary()
            self.system_output.setPlainText(summary)
            self._set_status("Hostname exposure summary updated.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Hostname exposure summary")

    def _about_dialog(self) -> None:
        cfg_path = getattr(self.config, "_config_path", lambda: "<unknown>")()
        text = (
            f"<b>TraceOff</b> – Privacy & Network Hardening Toolkit<br>"
            f"Version: {__version__}<br>"
            f"Config file: {cfg_path}<br><br>"
            "Use this GUI for quick inspection and safe actions.<br>"
            "For advanced operations and auto-fix workflows, prefer the CLI."
        )
        dlg = QMessageBox(self)
        dlg.setWindowTitle("About TraceOff")
        dlg.setTextFormat(Qt.RichText)
        dlg.setText(text)
        dlg.exec()

    def _update_check(self) -> None:
        self._set_status("Checking for TraceOff updates…")
        try:
            msg = check_updates(__version__)
            self.system_output.append(msg)
            self._set_status("Update check complete.")
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Update check")


# ==== Entry point =========================================================


def gui_entry() -> None:
    """
    Entry point used by `traceoff gui` CLI command.

    A failure here should print a clear message to stderr,
    but usually any runtime errors are handled by the window.
    """
    app = QApplication(sys.argv)
    try:
        config = TraceOffConfig.load_or_default()
        window = TraceOffMainWindow(config=config)
    except Exception as exc:  # noqa: BLE001
        # Last-resort error handler if even window creation fails.
        logger.exception("Failed to start TraceOff GUI: %s", exc)
        QMessageBox.critical(
            None,
            "Startup Error",
            "TraceOff GUI failed to start.\n\n"
            "Check your Python environment and configuration.\n"
            "See log output for more details.",
        )
        sys.exit(1)

    window.show()
    sys.exit(app.exec())
