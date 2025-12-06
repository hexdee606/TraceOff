"""
Secure update channel placeholder.

Future plan:
✔ Check remote signed manifests
✔ Validate GPG signatures
✔ Offer safe optional updates
"""

import requests
from ..core.logger import get_logger

logger = get_logger(__name__)

UPDATE_URL = "https://raw.githubusercontent.com/hexdee606/TraceOff/main/RELEASE.json"


def check_updates(current_version: str) -> str:
    try:
        r = requests.get(UPDATE_URL, timeout=5)
        data = r.json()
    except Exception():
        return "⚠ Update check unavailable."

    latest = data.get("latest", current_version)

    if latest > current_version:
        return f"⬆ Update available: {latest} (current: {current_version})"
    return "✔ Your version is up to date."
