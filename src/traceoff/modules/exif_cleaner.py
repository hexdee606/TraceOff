"""
File metadata (EXIF) scanning and cleaning module.

This module optionally uses `piexif` to remove EXIF metadata
from image files. If the dependency is not installed, it will
gracefully fall back with a helpful message.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List

from ..core.config import TraceOffConfig
from ..core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExifCleaner:
    """
    Scan and remove EXIF metadata from image files.

    Attributes:
        config:
            Shared TraceOff configuration instance.
    """

    config: TraceOffConfig

    # Supported image file extensions for EXIF processing.
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".tiff"}

    def _iter_files(self, path: Path, recursive: bool) -> List[Path]:
        """
        Collect image files under a given path.

        Args:
            path:
                Root file or directory path.
            recursive:
                Whether to recurse into subdirectories.

        Returns:
            List of Path objects for candidate image files.
        """
        files: List[Path] = []
        if path.is_file():
            if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                files.append(path)
        elif path.is_dir():
            if recursive:
                for p in path.rglob("*"):
                    if p.is_file() and p.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                        files.append(p)
            else:
                for p in path.iterdir():
                    if p.is_file() and p.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                        files.append(p)
        return files

    def scan(self, path: str, recursive: bool = True) -> str:
        """
        Scan files for potential EXIF metadata.

        Args:
            path:
                File or directory path to scan.
            recursive:
                Recurse into subdirectories if True.

        Returns:
            Human-readable summary string.
        """
        root = Path(path).expanduser()
        files = self._iter_files(root, recursive=recursive)

        lines: List[str] = []
        lines.append(f"=== TraceOff: EXIF Scan for {root} ===")

        if not files:
            lines.append("No supported image files found.")
            return "\n".join(lines)

        try:
            import piexif  # type: ignore  # noqa: F401
        except ImportError:
            lines.append("EXIF support not installed (missing 'piexif').")
            lines.append("Install with: pip install 'traceoff[exif]'")
            lines.append(f"Found {len(files)} candidate image files.")
            return "\n".join(lines)

        # For now we don’t output detailed EXIF content to keep it simple.
        lines.append(f"Found {len(files)} candidate image files.")
        lines.append("These files may contain EXIF (including GPS) metadata.")
        lines.append("Use 'traceoff exif clean' to remove EXIF where possible.")
        return "\n".join(lines)

    def clean(self, path: str, recursive: bool = True, backup: bool = True) -> str:
        """
        Remove EXIF metadata from supported image files.

        Args:
            path:
                File or directory path to clean.
            recursive:
                Recurse into subdirectories if True.
            backup:
                Create backup copies before modifying files.

        Returns:
            Human-readable summary of the cleanup operation.
        """
        root = Path(path).expanduser()
        files = self._iter_files(root, recursive=recursive)

        lines: List[str] = []
        lines.append(f"=== TraceOff: EXIF Clean for {root} ===")

        if not files:
            lines.append("No supported image files found.")
            return "\n".join(lines)

        try:
            import piexif  # type: ignore
        except ImportError:
            lines.append("EXIF support not installed (missing 'piexif').")
            lines.append("Install with: pip install 'traceoff[exif]'")
            return "\n".join(lines)

        import piexif  # type: ignore  # noqa: E402

        cleaned = 0
        failed = 0

        for img_path in files:
            logger.info("Cleaning EXIF: %s", img_path)
            if backup:
                backup_path = img_path.with_suffix(img_path.suffix + ".bak")
                if not backup_path.exists():
                    try:
                        shutil.copy2(img_path, backup_path)
                    except OSError as exc:
                        logger.warning("Failed to create backup for %s: %s", img_path, exc)

            try:
                # Load EXIF and then write an empty EXIF payload.
                _ = piexif.load(str(img_path))
                empty_exif = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
                exif_bytes = piexif.dump(empty_exif)
                piexif.insert(exif_bytes, str(img_path))
                cleaned += 1
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to clean EXIF on %s: %s", img_path, exc)
                failed += 1

        lines.append(f"Processed {len(files)} file(s).")
        lines.append(f"Successfully cleaned: {cleaned}")
        if failed:
            lines.append(f"Failed to clean: {failed}")
        if backup:
            lines.append("Backups created with '.bak' extension where possible.")

        return "\n".join(lines)
