"""
Graphical user interface for TraceOff (PySide6).

This GUI provides a simple tabbed interface over the main
TraceOff features:

- Privacy checkup (text + JSON)
- MAC spoofing (single change)
- EXIF scan & clean
- Firewall, DNS and IPv6 inspection
- Wi-Fi & hostname exposure inspection
- About & update check

Note:
    Long-running operations (like checkup) are executed
    directly; for most environments they are quick enough.
    If you notice the UI freezing, a future version can
    move heavy actions to background threads.
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
    """

    def __init__(self, config: Optional[TraceOffConfig] = None) -> None:
        super().__init__()
        self.config = config or TraceOffConfig.load_or_default()
        self.setWindowTitle(f"TraceOff GUI – v{__version__}")
        self.resize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout()
        central.setLayout(root_layout)

        header = QLabel(f"<h2>TraceOff – Privacy & Network Hardening</h2>")
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

    # ==== Error handling helpers ==========================================

    def _show_error(self, title: str, message: str, details: Optional[str] = None) -> None:
        """
        Show an error dialog with optional details.
        """
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle(title)
        dlg.setText(message)
        if details:
            dlg.setDetailedText(details)
        dlg.exec()

    def _handle_exception(self, exc: Exception, context: str) -> None:
        """
        Map internal exceptions to user-friendly dialogs.
        """
        if isinstance(exc, PrivilegeError):
            self._show_error(
                "Privilege Error",
                f"This action requires elevated privileges.\n\nContext: {context}",
                str(exc),
            )
        elif isinstance(exc, CommandExecutionError):
            self._show_error(
                "Command Failed",
                f"A required system command failed.\n\nContext: {context}",
                f"{exc}\n\nstderr:\n{getattr(exc, 'stderr', '')}",
            )
        elif isinstance(exc, ConfigError):
            self._show_error(
                "Configuration Error",
                "There is a problem with your TraceOff configuration.",
                str(exc),
            )
        elif isinstance(exc, TraceOffError):
            self._show_error("TraceOff Error", str(exc))
        else:
            logger.exception("Unhandled exception in GUI: %s", exc)
            self._show_error(
                "Unexpected Error",
                "An unexpected error occurred. See logs for details.",
                repr(exc),
            )

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
        try:
            builder = PrivacyReportBuilder(config=self.config)
            text = builder.render_human_readable()
            self.privacy_output.setPlainText(text)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Running privacy checkup (text)")

    def _privacy_run_check_json(self) -> None:
        """
        Run full privacy checkup and show JSON output.
        """
        try:
            builder = PrivacyReportBuilder(config=self.config)
            text = builder.render_json(indent=2)
            # Pretty JSON in the editor
            parsed = json.loads(text)
            pretty = json.dumps(parsed, indent=2)
            self.privacy_output.setPlainText(pretty)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Running privacy checkup (JSON)")

    def _privacy_show_ip(self) -> None:
        """
        Show quick IP + location summary.
        """
        try:
            checker = IpLeakChecker(config=self.config)
            summary = checker.build_location_summary()
            self.privacy_output.setPlainText(summary)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Fetching public IP & location")

    # ==== MAC tab =========================================================

    def _init_mac_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        form = QFormLayout()

        self.mac_iface_input = QLineEdit()
        if self.config.default_interface:
            self.mac_iface_input.setText(self.config.default_interface)
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
            self._show_error("Input Error", "Please specify a network interface (e.g., wlan0).")
            return

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
        Open a file/folder selection dialog for EXIF operations.
        """
        path = QFileDialog.getExistingDirectory(self, "Select directory")
        if path:
            self.exif_path_input.setText(path)

    def _exif_scan(self) -> None:
        path = self.exif_path_input.text().strip()
        if not path:
            self._show_error("Input Error", "Please select a file or directory to scan.")
            return
        try:
            cleaner = ExifCleaner(config=self.config)
            summary = cleaner.scan(path=path, recursive=self.exif_recursive.isChecked())
            self.exif_output.setPlainText(summary)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "EXIF scan")

    def _exif_clean(self) -> None:
        path = self.exif_path_input.text().strip()
        if not path:
            self._show_error("Input Error", "Please select a file or directory to clean.")
            return
        try:
            cleaner = ExifCleaner(config=self.config)
            summary = cleaner.clean(
                path=path,
                recursive=self.exif_recursive.isChecked(),
                backup=self.exif_backup.isChecked(),
            )
            self.exif_output.setPlainText(summary)
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
        try:
            manager = FirewallManager(config=self.config)
            status = manager.get_status()
            self.network_output.setPlainText(status)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Firewall status")

    def _fw_apply_profile(self, profile: str) -> None:
        dry_run = self.fw_dry_run.isChecked()
        try:
            manager = FirewallManager(config=self.config)
            manager.apply_profile(profile_name=profile, dry_run=dry_run)
            text = f"Requested firewall profile '{profile}' apply (dry_run={dry_run})."
            self.network_output.append(text)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, f"Apply firewall profile '{profile}'")

    def _dns_check(self) -> None:
        try:
            checker = DnsLeakChecker(config=self.config)
            summary = checker.build_human_summary()
            self.network_output.setPlainText(summary)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "DNS leak check")

    def _ipv6_status(self) -> None:
        try:
            mgr = Ipv6Manager(config=self.config)
            result = mgr.build_status_check()
            self.network_output.setPlainText(
                "=== IPv6 Status ===\n"
                f"{result.summary}\n\n"
                f"Details: {result.details}"
            )
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "IPv6 status")

    def _ipv6_toggle(self, disable: bool) -> None:
        """
        IPv6 enable/disable via sysctl in 'dry-run' mode from the GUI
        to avoid surprising the user. For real changes, prefer CLI.
        """
        try:
            mgr = Ipv6Manager(config=self.config)
            if disable:
                mgr.disable_ipv6(dry_run=True)
                msg = "Requested IPv6 disable (dry-run only). Use CLI for real changes."
            else:
                mgr.enable_ipv6(dry_run=True)
                msg = "Requested IPv6 enable (dry-run only). Use CLI for real changes."
            self.network_output.append(msg)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "IPv6 toggle (dry-run)")

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
        try:
            mgr = WifiPrivacyManager(config=self.config)
            summary = mgr.build_human_summary()
            self.system_output.setPlainText(summary)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Wi-Fi privacy summary")

    def _hostname_summary(self) -> None:
        try:
            mgr = HostnameManager(config=self.config)
            summary = mgr.build_human_summary()
            self.system_output.setPlainText(summary)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Hostname exposure summary")

    def _about_dialog(self) -> None:
        cfg_path = self.config._config_path()  # type: ignore[attr-defined]
        text = (
            f"<b>TraceOff</b> – Privacy & Network Hardening Toolkit<br>"
            f"Version: {__version__}<br>"
            f"Config file: {cfg_path}<br><br>"
            "Use this GUI for quick inspection and safe actions.<br>"
            "For advanced operations and auto-fix, prefer the CLI."
        )
        dlg = QMessageBox(self)
        dlg.setWindowTitle("About TraceOff")
        dlg.setTextFormat(Qt.RichText)
        dlg.setText(text)
        dlg.exec()

    def _update_check(self) -> None:
        try:
            msg = check_updates(__version__)
            self.system_output.append(msg)
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc, "Update check")


# ==== Entry point =========================================================


def gui_entry() -> None:
    """
    Entry point used by `traceoff gui` CLI command.
    """
    app = QApplication(sys.argv)
    config = TraceOffConfig.load_or_default()
    window = TraceOffMainWindow(config=config)
    window.show()
    sys.exit(app.exec())
