# TraceOff 
> **🔐 TraceOff — Privacy & Network-Hardening Toolkit for Security-Focused Systems**

---

<div align="center">

![GitHub License](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Repo Size](https://img.shields.io/github/repo-size/hexdee606/TraceOff)
![Status](https://img.shields.io/badge/status-active-success)
![Platform](https://img.shields.io/badge/platform-Linux-orange)
![Security](https://img.shields.io/badge/category-Privacy%20%2F%20Security-darkred)

---

</div>

## 📌 Overview

TraceOff is a cybersecurity and OPSEC utility for Linux-based privacy systems such as **Kali**, **Parrot OS**, **Qubes**, or OPSEC-clean configurations.

It provides a modular framework for:

* Reducing tracking surface
* Preventing location & DNS leaks
* Scrubbing metadata
* Hardening basic networking exposure
* Rotating identifiers (MAC-based identity reduction)

Designed with:

* Object-oriented architecture
* Flexible plugin-based privacy checks
* JSON or human-readable reporting
* Safe errors and guided remediation

---

## 🔧 Core Features

| Category              | Feature                                            |
| --------------------- | -------------------------------------------------- |
| 🔍 Identity Surface   | MAC spoofing + rotation, hostname broadcast checks |
| 🌍 Network Exposure   | IP leak analysis, DNS leak detection, IPv6 status  |
| 🛡 Firewall Hardening | UFW-based reporting                                |
| 📶 Wi-Fi Privacy      | Known networks + auto-connect risk                 |
| 🖼 Metadata Hygiene   | EXIF metadata scanning and removal                 |
| 🧠 Structured Results | JSON reporting for automation                      |
| ⚠ Friendly UX         | Clear hints when something fails                   |

---

## 🖼 Screenshot Placeholder

```
┌───────────────────────────────────────┐
│         TRACEOFF CHECKUP REPORT       │
├───────────────────────────────────────┤
│ WARNING: Public IP is exposed         │
│ OK: Firewall active                   │
│ WARNING: MAC address vendor identity  │
└───────────────────────────────────────┘
```

*Screenshots will be added after UI polish.*

---

## 🛠 Installation

```bash
git clone https://github.com/hexdee606/TraceOff.git
cd TraceOff
pip install -e .
```

Install optional dependencies:

```bash
sudo apt install ufw network-manager piexif jq -y
```

---

## 🧭 Usage Examples

### Run full privacy check:

```bash
traceoff privacy checkup
```

### JSON Mode (for logs, SIEM, scripts):

```bash
traceoff privacy checkup --format json | jq .
```

### Randomize MAC (one time):

```bash
sudo traceoff mac spoof-once --iface wlan0
```

### Rotate MAC every 5 minutes:

```bash
sudo traceoff mac rotate --iface wlan0 --interval 300
```

---

## ⚙️ Configuration System

TraceOff stores persistent config in:

```
~/.config/traceoff/config.json
```

Use:

```bash
traceoff config-path
```

to see it.

### 🧩 Example Config File

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

### 🔑 Supported Keys

| Key                     | Type              | Purpose                                         |            |                    |
| ----------------------- | ----------------- | ----------------------------------------------- | ---------- | ------------------ |
| `log_level`             | `"DEBUG"          | "INFO"                                          | "WARNING"` | Controls verbosity |
| `auto_backup`           | boolean           | Backup original images when removing EXIF       |            |                    |
| `default_interface`     | string            | Network interface used if CLI not provided      |            |                    |
| `mac.vendor_like`       | boolean           | Whether generated MACs use real vendor prefixes |            |                    |
| `mac.rotation_interval` | integer (seconds) | Default MAC rotation time                       |            |                    |
| `privacy.auto_fix`      | boolean           | Enables experimental auto-hardening mode        |            |                    |

> 🧪 **Note:** `auto_fix` is optional preview functionality.
> Future versions will support:
> `traceoff privacy autofix --yes-i-understand`.

---

## 👷 Project Structure

```
traceoff/
 ├─ core/
 ├─ modules/
 ├─ checks/
 ├─ utils/
 ├─ tests/
 ├─ cli.py
 ├─ pyproject.toml
 └─ README.md
```

---

## 🧪 Development Mode

```bash
pip install -r requirements-dev.txt
pytest -v
```

---

## 📍 Roadmap

| Status         | Feature                               |
| -------------- | ------------------------------------- |
| 🟢 Done        | Registry-based modular privacy checks |
| 🟢 Done        | JSON reporting                        |
| 🟢 Done        | MAC rotation                          |
| 🟡 In Progress | Auto-fix privacy mode                 |
| 🟡 In Progress | Plugin system                         |
| 🔵 Planned     | GUI (Qt or Electron)                  |
| 🔵 Planned     | Secure Update Channel & Signing       |

---

## 🔏 Legal Notice

TraceOff is intended for:

✔ Personal privacy
✔ Educational research
✔ Legal network security testing

🚫 **Unauthorized use on networks you do not own or control is illegal.**

You are responsible for compliance with laws.

---

## 🧾 License

Licensed under the **MIT License**.

---

## 👤 Author

**Dipen**
Security Engineer · Automation Specialist
🔗 GitHub: [https://github.com/hexdee606](https://github.com/hexdee606)
📝 Medium: [https://medium.com/@dipenc245](https://medium.com/@dipenc245)

---

## ⭐ Support the Project

If TraceOff helps your privacy journey —
star ⭐ the project to support development.
