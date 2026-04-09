from __future__ import annotations

from src.config.constants import MAX_CHUNK_BYTES, MIN_CHUNK_BYTES, UNIT_MAP
from src.utils.errors import InvalidSizeError


def parse_size(value: str, unit: str) -> int:
    """
    Parse a size string and unit into bytes.

    Args:
        value: Numeric string (e.g., "500", "1.5").
        unit: One of "KB", "MB", "GB".

    Returns:
        Size in bytes as an integer.

    Raises:
        InvalidSizeError: If value is not a positive number, unit is unknown,
                          or result is outside the allowed range (1MB–10GB).
    """
    if unit not in UNIT_MAP:
        raise InvalidSizeError(f"Unknown unit '{unit}'. Must be one of: {list(UNIT_MAP)}")

    try:
        numeric = float(value)
    except (ValueError, TypeError):
        raise InvalidSizeError(f"Invalid size value '{value}'. Must be a positive number.")

    if numeric <= 0:
        raise InvalidSizeError(f"Size must be a positive number, got {numeric}.")

    chunk_bytes = int(numeric * UNIT_MAP[unit])

    if chunk_bytes < MIN_CHUNK_BYTES:
        raise InvalidSizeError(
            f"Chunk size {chunk_bytes:,} bytes is below the minimum of {MIN_CHUNK_BYTES:,} bytes (1 MB)."
        )

    if chunk_bytes > MAX_CHUNK_BYTES:
        raise InvalidSizeError(
            f"Chunk size {chunk_bytes:,} bytes exceeds the maximum of {MAX_CHUNK_BYTES:,} bytes (10 GB)."
        )

    return chunk_bytes


def format_size(byte_count: int) -> str:
    """Return a human-readable representation of a byte count."""
    if byte_count >= 1024 ** 3:
        return f"{byte_count / (1024 ** 3):.2f} GB"
    if byte_count >= 1024 ** 2:
        return f"{byte_count / (1024 ** 2):.2f} MB"
    if byte_count >= 1024:
        return f"{byte_count / 1024:.2f} KB"
    return f"{byte_count} B"
