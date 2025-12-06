# 📜 Changelog – TraceOff

All notable changes to this project will be documented in this file.

This project aims to follow [Semantic Versioning](https://semver.org/):

- `MAJOR` – Breaking changes
- `MINOR` – New features, backwards compatible
- `PATCH` – Bug fixes, no API changes

---

## [3.0.0] – 2025-01-01

### 🎯 Major Release

TraceOff 3.0.0 is a full redesign of the earlier AMC tooling into a modular, extensible privacy & network-hardening toolkit.

#### ✨ Added

- **New modular architecture**
  - `core/` for configuration, models, exceptions, logging.
  - `modules/` for specific features (MAC, EXIF, IPv6, firewall, etc.).
  - `checks/` for privacy checks with a central `registry`.
  - `gui/` for the PySide6-based graphical UI.

- **Registry-based privacy checks**
  - `ip_leak` – Public IP + geolocation.
  - `dns_leak` – DNS server summary and potential leak hints.
  - `ipv6_status` – IPv6 enablement & tracking risk.
  - `wifi_privacy` – Known Wi-Fi networks and auto-connect.
  - `hostname_exposure` – Hostname + Avahi/mDNS broadcasting.
  - `firewall_status` – UFW status & basic exposure risk.
  - `mac_exposure` – Interface MAC address tracking risk.

- **Reporting**
  - `traceoff privacy checkup` – Full privacy checkup with text report.
  - `traceoff privacy checkup --format json` – JSON output for automation and SIEM.

- **MAC tools**
  - `traceoff mac spoof-once` – One-shot MAC spoofing with vendor-like/random modes.
  - `traceoff mac rotate` – Periodic MAC rotation at configurable intervals.

- **EXIF tools**
  - `traceoff exif scan PATH` – Scan images for EXIF metadata.
  - `traceoff exif clean PATH` – Clean EXIF metadata with optional backups.

- **Firewall integration (UFW)**
  - `traceoff firewall status` – Show UFW status.
  - `traceoff firewall set PROFILE` – Apply named profiles (e.g., `public`, `home`) with optional `--dry-run`.

- **Wi-Fi & Hostname**
  - `traceoff wifi list-known` – Show known Wi-Fi networks & auto-connect flags.
  - `traceoff hostname report` – Show hostname, FQDN, and Avahi/mDNS status.

- **CLI experience**
  - Central error handler with:
    - `PrivilegeError` (missing root/sudo).
    - `CommandExecutionError` (system tool failures).
    - `ConfigError` (bad or missing config).
  - Clear hints and user-facing messages instead of raw tracebacks.
  - `traceoff version` – Human-friendly version & metadata.
  - `traceoff about` – Tool description, dependency versions, config path.

- **GUI**
  - New PySide6 GUI (`traceoff gui`) with:
    - Privacy Checkup tab (text / JSON).
    - MAC tools tab (interface, vendor-like, dry-run).
    - EXIF tools tab (scan, clean, recursive, backup).
    - Network & Firewall tab (UFW, DNS, IPv6).
    - System & Info tab (Wi-Fi, hostname, about, update check).
  - Error dialogs with context and hints.
  - Status bar updates for each operation.

- **Configuration**
  - JSON config at `~/.config/traceoff/config.json`.
  - Fields for:
    - `log_level`
    - `default_interface`
    - `auto_backup`
    - `mac.vendor_like`
    - `mac.rotation_interval`
    - `privacy.auto_fix` (preview).

- **Plugins**
  - Simple plugin loader from `~/.config/traceoff/plugins/*.py`.
  - Plugins can register new checks via `registry.register(...)`.

- **Update-check channel**
  - `traceoff update-check` uses `RELEASE.json` hosted in the repo to:
    - Compare current and latest version.
    - Provide simple text message on up-to-date / update available.

#### 🔁 Changed

- Replaced previous AMC 2.x layout with a clean `src/traceoff` package layout.
- Refined CLI structure with Typer subcommands (`mac`, `privacy`, `exif`, `firewall`, `wifi`, `hostname`).

#### 🧹 Fixed / Hardened

- More robust handling when system tools (e.g., `ufw`, `nmcli`) are missing.
- Graceful handling of unsupported environments (e.g., WSL, minimal containers).
- Unified error handling across CLI and GUI.

---

## [2.x.x] – (Legacy AMC versions)

Older AMC versions were early, less modular experiments in privacy tooling.

Key characteristics:

- Basic MAC spoofing scripts.
- Limited IP/DNS inspection.
- Less consistent error handling and structure.

These versions are **no longer supported** and have been superseded by TraceOff `3.x`.

---

## [Unreleased]

Planned / in-progress ideas:

- ⚙ Auto-fix engine improvements with safe, guided remediation flows.
- 🔌 Plugin API documentation and examples.
- 🖥 GUI enhancement (theming, icons, check severity visualization).
- 🔐 Optional signature verification for update metadata.

---

If you make a change:

- Add a new section under `[Unreleased]` or a new `[x.y.z]` block.
- Briefly describe what changed (Added / Changed / Fixed / Security).
- Keep entries concise but meaningful for users.
