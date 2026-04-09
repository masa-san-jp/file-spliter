from __future__ import annotations

from pathlib import Path

from src.config.constants import INPUT_FOLDER_NAME, LOGS_FOLDER_NAME, OUTPUT_FOLDER_NAME


def app_root() -> Path:
    """Return the application root directory (parent of src/)."""
    return Path(__file__).parent.parent.parent


def input_dir() -> Path:
    return app_root() / INPUT_FOLDER_NAME


def output_dir() -> Path:
    return app_root() / OUTPUT_FOLDER_NAME


def logs_dir() -> Path:
    return app_root() / LOGS_FOLDER_NAME


def ensure_dir(path: Path) -> Path:
    """Create directory if it does not exist; return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def unique_output_subdir(base: Path, stem: str) -> Path:
    """
    Return a unique subdirectory path under base for the given stem.
    Appends an incrementing suffix if the directory already exists.
    """
    candidate = base / stem
    if not candidate.exists():
        return candidate

    counter = 1
    while True:
        candidate = base / f"{stem}_{counter:03d}"
        if not candidate.exists():
            return candidate
        counter += 1


def is_hidden_or_temp(path: Path) -> bool:
    """Return True if the file should be excluded (hidden or temp file)."""
    name = path.name
    return name.startswith(".") or name.startswith("~") or name.endswith(".tmp")
