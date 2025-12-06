# TraceOff Logo

> **🔐 TraceOff — Privacy & Network-Hardening Toolkit for Security-Focused Systems**

---

<div align="center">

![GitHub License](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Status](https://img.shields.io/badge/status-stable-success)
![Platform](https://img.shields.io/badge/platform-Linux-orange)
![Security](https://img.shields.io/badge/category-Privacy%20%2F%20Security-darkred)

</div>

---

## 📌 Overview

**TraceOff** is a privacy and network-hardening toolkit designed for:

- Kali Linux, Parrot OS, and other security-focused distros  
- OPSEC-minded users and red teamers  
- Anyone who wants **less tracking**, **less metadata leakage**, and **safer defaults**

It provides:

- MAC spoofing & rotation  
- Public IP, DNS, IPv6, Wi-Fi, hostname & firewall checks  
- EXIF metadata scanning and cleaning  
- A registry-based privacy check framework with JSON output  
- A GUI (PySide6, optional) and rich CLI  
- Auto-fix preview mode (CLI)  
- Plugin loading for custom checks & tools  
- Optional update-check channel

---

## ✨ Major Features

### 🕵️ Identity Surface

- MAC address spoofing (`traceoff mac spoof-once`)
- MAC rotation over time (`traceoff mac rotate`)
- Local hostname / mDNS exposure reporting
- Wi-Fi known networks + auto-connect risk

### 🌍 Network Exposure

- Public IP + geolocation summary
- DNS leak detection
- IPv6 status and privacy assessment
- UFW-based firewall exposure reporting

### 🖼 Metadata Hygiene

- EXIF metadata scanning
- Batch EXIF cleaning with optional backups

### 📊 Reporting & Automation

- Human-readable text reports
- Machine-readable JSON (`--format json`)
- Central check registry + consistent `CheckResult` model

### 🧠 UX & Safety

- Friendly CLI errors with hints (no ugly tracebacks for common issues)
- GUI with per-action error dialogs and status bar
- Dry-run modes for risky actions (IPv6, firewall, MAC)

---

## 🧱 Architecture Snapshot

```text
src/traceoff
 ├── cli.py              # Main Typer CLI entrypoint
 ├── core/
 │    ├── config.py      # JSON config handling
 │    ├── models.py      # CheckResult, PrivacyReport, etc.
 │    ├── exceptions.py  # TraceOffError and subclasses
 │    ├── logger.py      # Logging helpers
 │    ├── plugin_loader.py # Plugin discovery
 │    └── updater.py     # Update-check logic (RELEASE.json)
 ├── modules/
 │    ├── mac_manager.py
 │    ├── ip_leak_checker.py
 │    ├── dns_leak_checker.py
 │    ├── ipv6_manager.py
 │    ├── exif_cleaner.py
 │    ├── firewall_manager.py
 │    ├── wifi_privacy.py
 │    ├── hostname_manager.py
 │    ├── privacy_report.py
 │    └── autofix_manager.py
 ├── checks/
 │    ├── base.py
 │    ├── registry.py
 │    ├── ip_check.py
 │    ├── dns_check.py
 │    ├── ipv6_check.py
 │    ├── wifi_check.py
 │    ├── hostname_check.py
 │    ├── firewall_check.py
 │    └── mac_check.py
 ├── gui/
 │    └── app.py         # PySide6 GUI
 ├── utils/
 │    ├── network.py
 │    └── shell.py
 └── README.md
````

---

## 🛠 Installation

### 1️⃣ Clone the repo

```bash
git clone https://github.com/hexdee606/TraceOff.git
cd TraceOff
```

### 2️⃣ Install core CLI

```bash
pip install -e .
```

This gives you:

* `traceoff` CLI
* All privacy checks
* EXIF, MAC, firewall, DNS, IPv6, Wi-Fi & hostname modules

### 3️⃣ Optional: GUI + extras

GUI (PySide6) and recommended extras:

```bash
pip install -e ".[gui,extra]"
```

Dev environment (tests, formatting, type checking):

```bash
pip install -e ".[gui,extra,dev]"
```

> Make sure you are in a virtual environment if you prefer isolated installs.

---

## 🚀 Quick Start

### CLI help

```bash
traceoff --help
```

### Version & metadata

```bash
traceoff version
traceoff about
```

### Full privacy checkup (text)

```bash
traceoff privacy checkup
```

### Full privacy checkup (JSON)

```bash
traceoff privacy checkup --format json
```

---

## 🧭 Command Reference (CLI)

### Global / Meta Commands

| Command                 | Description                                 |
| ----------------------- | ------------------------------------------- |
| `traceoff version`      | Show version, author, license, Python info  |
| `traceoff about`        | Show tool description + dependency versions |
| `traceoff config-path`  | Show current config file path               |
| `traceoff update-check` | Check for updates via RELEASE.json          |
| `traceoff gui`          | Launch PySide6 GUI (if installed)           |

---

### Privacy Commands

Namespace: `traceoff privacy`

| Command                            | Description                            |
| ---------------------------------- | -------------------------------------- |
| `traceoff privacy checkup`         | Run all registered privacy checks      |
| `traceoff privacy checkup -f json` | Same, but JSON output                  |
| `traceoff privacy location-check`  | Public IP + ASN + geolocation summary  |
| `traceoff privacy dns-check`       | DNS configuration & leak heuristics    |
| `traceoff privacy ipv6-status`     | IPv6 enablement status & risk summary  |
| `traceoff privacy ipv6-disable`    | Temporarily disable IPv6 via sysctl    |
| `traceoff privacy ipv6-enable`     | Re-enable IPv6 via sysctl              |
| `traceoff privacy autofix`         | Interactive auto-fix (preview feature) |

---

### MAC Tools

Namespace: `traceoff mac`

| Command                             | Description                                   |
| ----------------------------------- | --------------------------------------------- |
| `traceoff mac spoof-once --iface X` | Change MAC once for interface X               |
| `traceoff mac spoof-once --dry-run` | Show what would change, without applying      |
| `traceoff mac rotate --iface X`     | Rotate MAC on X at a given interval (seconds) |

> ⚠ These usually require root privileges on Linux (`sudo`).

---

### EXIF Metadata

Namespace: `traceoff exif`

| Command                      | Description                                 |
| ---------------------------- | ------------------------------------------- |
| `traceoff exif scan PATH`    | Scan images under PATH for EXIF metadata    |
| `traceoff exif clean PATH`   | Remove EXIF metadata from images under PATH |
| `--recursive/--no-recursive` | Whether to recurse into subdirectories      |
| `--backup/--no-backup`       | Create backups before cleaning              |

---

### Firewall (UFW)

Namespace: `traceoff firewall`

| Command                         | Description                            |
| ------------------------------- | -------------------------------------- |
| `traceoff firewall status`      | Show UFW status output                 |
| `traceoff firewall set PROFILE` | Apply profile (e.g., `public`, `home`) |
| `--dry-run`                     | Print intended UFW commands only       |

> ⚠ Requires `ufw` and root to apply changes.

---

### Wi-Fi & Hostname

Namespace: `traceoff wifi` / `traceoff hostname`

| Command                    | Description                                     |
| -------------------------- | ----------------------------------------------- |
| `traceoff wifi list-known` | Show known Wi-Fi networks and auto-connect info |
| `traceoff hostname report` | Show hostname + FQDN + Avahi/mDNS status        |

> Uses tools like `nmcli` and `systemctl` if present.
> If missing, checks degrade gracefully and report INFO status.

---

## 🖥 GUI (PySide6)

TraceOff includes a **Qt-based GUI** (optional dependency).

### Install GUI dependencies

```bash
pip install -e ".[gui,extra]"
```

### Launch GUI

```bash
traceoff gui
```

GUI tabs include:

* **Privacy Checkup**

  * Run full checkup (text / JSON)
  * Quick IP + location

* **MAC Tools**

  * Interface field
  * Vendor-like toggle
  * Dry-run mode
  * One-shot spoof

* **EXIF Tools**

  * Browse path
  * Recursive + backup switches
  * Scan & clean actions

* **Network & Firewall**

  * UFW status & profile apply (with optional dry-run)
  * DNS leak check
  * IPv6 status & (dry-run) enable/disable

* **System & Info**

  * Wi-Fi privacy summary
  * Hostname exposure summary
  * About dialog
  * Update check via `RELEASE.json`

All GUI actions:

* Are wrapped in error handling
* Show friendly dialogs instead of raw tracebacks
* Update the status bar with short messages

---

## ⚙ Configuration (config.json)

Config path:

```bash
traceoff config-path
```

By default:

```text
~/.config/traceoff/config.json
```

### Example

```json
{
  "log_level": "INFO",
  "auto_backup": true,
  "default_interface": "wlan0",
  "mac": {
    "vendor_like": true,
    "rotation_interval": 600
  },
  "privacy": {
    "auto_fix": false
  }
}
```

### Common Keys

| Key / Path              | Type   | Meaning                                     |
| ----------------------- | ------ | ------------------------------------------- |
| `log_level`             | string | `DEBUG`, `INFO`, `WARNING`, `ERROR`         |
| `auto_backup`           | bool   | Backup originals when cleaning EXIF         |
| `default_interface`     | string | Fallback interface for MAC operations       |
| `mac.vendor_like`       | bool   | Prefer vendor-like MAC prefixes if `true`   |
| `mac.rotation_interval` | int    | Default rotation interval in seconds        |
| `privacy.auto_fix`      | bool   | Opt-in to more automated fix flows (future) |

---

## 🔌 Plugins

TraceOff can load plugins from:

```text
~/.config/traceoff/plugins/*.py
```

Any plugin module imported this way can:

* Register new privacy checks (`registry.register(MyCheck)`)
* Add new CLI helpers (if you wire them)
* Extend autofix logic

Basic pattern:

```python
# ~/.config/traceoff/plugins/my_custom_check.py
from traceoff.checks.base import PrivacyCheck
from traceoff.checks.registry import registry
from traceoff.core.models import CheckResult, CheckStatus

class MyCustomCheck(PrivacyCheck):
    name = "my_custom_check"
    description = "Demo plugin check."

    def run(self) -> CheckResult:
        return CheckResult(
            name=self.name,
            status=CheckStatus.INFO,
            summary="This is a plugin-provided check.",
            details={"plugin": True}
        )

registry.register(MyCustomCheck)
```

Restart CLI/GUI to see the new check in `privacy checkup`.

---

## 🔄 Updates & `RELEASE.json`

`traceoff update-check` uses a small JSON manifest hosted at:

```text
https://raw.githubusercontent.com/hexdee606/TraceOff/main/RELEASE.json
```

This file declares:

* Latest version
* Optional notes and links

See below for the latest format.

---

## ⚠ Legal / Ethical Use

TraceOff is intended for:

* Personal privacy & OPSEC
* Education & research
* Controlled security testing

**Do not use it for illegal or unauthorized activities.**
You are responsible for complying with all applicable laws.

---

## 🧾 License

Licensed under the **MIT License**.
See the `LICENSE` file for full text.

---

## 👤 Author

**Dipen**
Senior Associate Quality Engineer & Security Enthusiast

* GitHub: [https://github.com/hexdee606](https://github.com/hexdee606)
* Medium: [https://medium.com/@dipenc245](https://medium.com/@dipenc245)

---

## ⭐ Support the Project

If you find TraceOff useful:

* ⭐ Star the repo
* 🐛 Report issues
* 🔧 Send PRs (checks, plugins, docs, UX improvements)

Stay private. Stay curious.
**TraceOff 3.0.0** 🛰️