# 🤝 Contributing to TraceOff

First off: thank you for considering contributing to TraceOff.  
This project exists to help people protect their privacy and understand their exposure — and contributions are always
welcome.

---

## 🧩 Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest new privacy checks or features
- 🔧 Improve code (cleanups, refactors, tests)
- 🌍 Enhance documentation (README, Wiki, examples)
- 🧪 Add test coverage
- 🧠 Propose better defaults / hardening strategies

---

## 🛠 Development Setup

1. **Fork** the repo on GitHub.
2. **Clone** your fork:

   ```bash
   git clone https://github.com/<your-username>/TraceOff.git
   cd TraceOff
   ```
3. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Linux/macOS
   # or
   .venv\Scripts\activate           # Windows
   ```

4. **Install in editable dev mode**:

   ```bash
   pip install -e ".[gui,extra,dev]"
   ```

   This installs:

    * Core CLI + modules
    * GUI (PySide6)
    * Extras (`piexif`, etc.)
    * Dev tools (`pytest`, `black`, `flake8`, `mypy`)

5. **Run basic checks**:

   ```bash
   traceoff version
   traceoff privacy checkup
   ```

---

## 📁 Project Layout (Quick Overview)

```text
src/traceoff
 ├── cli.py              # Typer CLI entrypoint
 ├── core/               # Config, models, logger, exceptions, plugins, updater
 ├── modules/            # Feature modules (MAC, IPv6, EXIF, firewall, etc.)
 ├── checks/             # Registered privacy checks
 ├── gui/                # PySide6 GUI
 ├── utils/              # Shared helpers (shell, network)
 └── ...
```

---

## 🧪 Tests

Run all tests:

```bash
pytest -v
```

Please add tests when:

* You fix a bug.
* You add new functionality.
* You change core behavior in `core/`, `modules/`, or `checks/`.

If your change is hard to test (e.g., depends heavily on system commands), you can:

* Abstract the command into a function in `utils/shell.py`.
* Add a test that mocks this function.

---

## 🎨 Code Style

* **Python**: Use `black` (configured in `pyproject.toml`).
* **Linting**: Use `flake8`.
* **Types**: Use `mypy` annotations gradually where it makes sense.

Suggested workflow:

```bash
black src tests
flake8 src tests
mypy src
pytest -v
```

---

## 🌱 Adding a New Privacy Check

1. Create a new file under `src/traceoff/checks/`:

   ```python
   # src/traceoff/checks/my_check.py
   from traceoff.checks.base import PrivacyCheck
   from traceoff.checks.registry import registry
   from traceoff.core.models import CheckResult, CheckStatus

   class MyCheck(PrivacyCheck):
       name = "my_check"
       description = "Short description of the risk being checked."

       def run(self) -> CheckResult:
           # your logic here
           return CheckResult(
               name=self.name,
               status=CheckStatus.INFO,
               summary="My check ran successfully.",
               details={"example": True},
           )

   registry.register(MyCheck)
   ```

2. Ensure it’s imported in `modules/privacy_report.py` if needed for registration side-effect (or rely on direct import
   from the checks package).

3. Add tests if possible.

4. Run:

   ```bash
   traceoff privacy checkup --format json
   ```

   Confirm your new check appears in the results.

---

## 🔌 Plugins vs Core

* If your idea is **generic** and improves privacy for most users → consider implementing it in core (`checks` and
  `modules`).
* If your idea is **very specific** (custom environment, lab, enterprise) → consider writing a plugin:

  ```python
  # ~/.config/traceoff/plugins/my_plugin_check.py
  ...
  ```

This is a good way to experiment before proposing a core feature.

---

## 🔐 Security Considerations

Because this is a security/privacy tool:

* Avoid introducing commands that:

    * Send data to remote servers without explicit consent.
    * Log sensitive data (IPs, filenames, metadata) unnecessarily.
* Be careful with:

    * Shell command construction (prefer argument lists and `utils.shell.run_command`).
    * Temporary files (clean them up, avoid world-readable sensitive files).
* If your change touches anything security-sensitive, briefly document your threat assumptions in the PR description.

---

## 📥 Pull Request Guidelines

1. **Small and focused** PRs are easier to review.
2. Provide a clear description:

    * What changed
    * Why it changed
    * How to test it
3. If your change affects user behavior, update:

    * `README.md`
    * `CHANGELOG.md`
    * `RELEASE.json` if it’s a notable release-level change
4. Make sure tests pass (or explain why they can’t in this PR).

---

## 💬 Communication

* For bugs/features: GitHub Issues.
* For security issues: **do not** open a public issue — see `SECURITY.md`.
* For questions/ideas: Issues or discussions (if enabled).

---

## 🙏 Thank You

Every small improvement — a typo fix, a better error message, a new check — helps make TraceOff more useful and safer
for everyone.
Thanks for contributing. ❤️