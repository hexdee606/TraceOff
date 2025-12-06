# 🔐 Security Policy

TraceOff is a privacy and network-hardening toolkit designed to help users reduce digital identity exposure. Because the project interacts with system components, networking, and metadata, responsible security reporting is critical.

---

## 🧾 Supported Versions

| TraceOff Version            | Status          |
| --------------------------- | --------------- |
| **3.0.x (Current)**         | ✅ Supported     |
| **2.x (Legacy AMC builds)** | ❌ Not supported |
| **1.x (Deprecated)**        | ❌ Not supported |

Only the latest `3.x` line receives patches and fixes.

---

## 🛡 What Qualifies as a Security Issue?

Valid security issues include:

* Unauthorized system modifications
* Privilege escalation or bypassing permission checks
* Remote command execution or injection
* Exposed sensitive metadata or unintended leaks
* Weak or dangerous defaults that compromise privacy

The following are **not** considered vulnerabilities:

* Missing features or enhancements
* Version detection false positives
* Cosmetic UI/UX issues
* Dependency warnings without exploitation potential

---

## 🚨 Reporting a Vulnerability

Please **do not report vulnerabilities publicly** (issues, pull requests, social platforms).

Instead, report privately via:

📧 Email: **[opensource.hexdee606@gmail.com](mailto:opensource.hexdee606@gmail.com)**

(Encrypted contact / PGP support planned.)

Include when possible:

* Description of the vulnerability
* Reproduction steps or proof-of-concept
* Expected vs actual behavior
* `traceoff version` output
* OS and environment details

Example format:

```
Title: Unprivileged firewall modification allowed

TraceOff Version: 3.0.0
OS: Kali Linux 2025.1
Severity: High

Steps:
1. Run: traceoff firewall set public (without sudo)
2. Command succeeds

Expected:
Privilege warning or rejection

Impact:
Unauthorized firewall modification could reduce system privacy.
```

---

## ⏱ Response Timeline

Once reported, you can expect:

| Stage                       | Estimated Time      |
| --------------------------- | ------------------- |
| Acknowledgment              | 48–72 hours         |
| Initial assessment & triage | 5–10 days           |
| Fix timeline provided       | After triage        |
| Patch release               | Depends on severity |

Severity-based priority:

| Severity    | Resolution Goal              |
| ----------- | ---------------------------- |
| 🚨 Critical | As soon as possible (hotfix) |
| ⚠ High      | Next planned release         |
| 🔧 Medium   | Future milestone             |
| 📄 Low      | May be deferred              |

---

## 💰 Compensation & Bounty Policy

TraceOff is a **fully open-source, non-funded and community-driven project.**

Because of this:

> **We DO NOT offer bug bounties, financial rewards, or paid compensation for vulnerability reports.**

However, we will:

* Credit ethical reporters (optional anonymous acknowledgement)
* Include acknowledgements in release notes for confirmed issues
* Support collaboration with researchers and educators

We deeply appreciate all contributions — financial or not — that improve the privacy and safety of others.

---

## 🔓 Disclosure Process

After validation:

1. A fix or mitigation is developed.
2. A new release is published.
3. Documentation, changelog, and release notes are updated.
4. (Optional) You are credited in acknowledgements.

Premature disclosure before a fix may put users at risk — please allow us time to patch.

---

## ⚖ Ethical Use Statement

TraceOff is intended for:

* Educational use
* Research
* Personal privacy and digital hygiene
* Security training and lawful penetration testing

It should **not** be used for:

* Surveillance
* Deanonymization of others
* Unauthorized access or network manipulation
* Any activity that violates law or user consent

Users are responsible for complying with laws in their country.

---

## ❤️ Thank You

We value and respect everyone helping make TraceOff safer, more resilient, and ethical.

Responsible reporting protects real people — and that makes you part of the mission.
