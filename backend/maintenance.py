from datetime import datetime, timezone
from pathlib import Path
import shutil


CLEANUP_PATHS = (
    Path("/tmp/kguard"),
    Path("/tmp/kguard-cache"),
)


def _directory_size(path: Path) -> int:
    total = 0

    if path.is_file():
        return path.stat().st_size

    if not path.exists():
        return 0

    for child in path.rglob("*"):
        try:
            if child.is_file():
                total += child.stat().st_size
        except OSError:
            continue

    return total


def _cleanup_directory(path: Path) -> dict:
    reclaimed_bytes = _directory_size(path)
    removed_files = 0
    removed_directories = 0

    if not path.exists():
        return {
            "target": path.name,
            "path": str(path),
            "removed_files": 0,
            "removed_directories": 0,
            "reclaimed_bytes": 0,
        }

    for child in list(path.iterdir()):
        try:
            if child.is_dir():
                shutil.rmtree(child)
                removed_directories += 1
            else:
                child.unlink()
                removed_files += 1
        except OSError:
            continue

    return {
        "target": path.name,
        "path": str(path),
        "removed_files": removed_files,
        "removed_directories": removed_directories,
        "reclaimed_bytes": reclaimed_bytes,
    }


def run_safe_cleanup() -> dict:
    items = [_cleanup_directory(path) for path in CLEANUP_PATHS]
    reclaimed_bytes = sum(item["reclaimed_bytes"] for item in items)

    return {
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reclaimed_bytes": reclaimed_bytes,
        "reclaimed_mb": round(reclaimed_bytes / 1024 / 1024, 2),
        "items": items,
        "preserved": [
            "wazuh-alerts-*",
            "wazuh-indexer-data",
            "security_events",
            "kubernetes_secrets",
            "application_database",
        ],
    }
