from __future__ import annotations

MIN_CHUNK_BYTES: int = 1 * 1024 * 1024        # 1 MB
MAX_CHUNK_BYTES: int = 10 * 1024 * 1024 * 1024  # 10 GB

UNIT_MAP: dict[str, int] = {
    "KB": 1024,
    "MB": 1024 * 1024,
    "GB": 1024 * 1024 * 1024,
}

AUDIO_EXTENSIONS: frozenset[str] = frozenset(
    {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
)

VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {".mp4", ".mov", ".mkv", ".avi", ".webm"}
)

MEDIA_EXTENSIONS: frozenset[str] = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS

AUDIO_MIME_PREFIXES: tuple[str, ...] = ("audio/",)
VIDEO_MIME_PREFIXES: tuple[str, ...] = ("video/",)
MEDIA_MIME_PREFIXES: tuple[str, ...] = AUDIO_MIME_PREFIXES + VIDEO_MIME_PREFIXES

READ_BUFFER_SIZE: int = 1 * 1024 * 1024  # 1 MB

INPUT_FOLDER_NAME: str = "分割前"
OUTPUT_FOLDER_NAME: str = "分割後"
LOGS_FOLDER_NAME: str = "logs"

MEDIA_SIZE_TOLERANCE_RATIO: float = 0.05  # 5%
