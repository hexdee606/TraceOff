"""
Simple plugin loader for TraceOff.

Loads user-provided modules for:
✔ new privacy checks
✔ new auto-fix actions
✔ future GUI extensions
"""

from pathlib import Path
import importlib.util
from ..core.logger import get_logger

logger = get_logger(__name__)

PLUGIN_PATH = Path("~/.config/traceoff/plugins").expanduser()


def load_plugins():
    """Load user plugins from plugin directory."""
    if not PLUGIN_PATH.exists():
        return

    for file in PLUGIN_PATH.glob("*.py"):
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore
            logger.info(f"Loaded plugin: {file.name}")
        except Exception as e:
            logger.error(f"Failed to load plugin '{file}': {e}")
