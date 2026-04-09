from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Literal

from src.config.constants import MEDIA_EXTENSIONS, MEDIA_MIME_PREFIXES


FileKind = Literal["media", "generic"]


def detect_kind(path: Path) -> FileKind:
    """
    Determine if a file is a media file (audio/video) or a generic file.

    Detection order:
    1. MIME type (via mimetypes module)
    2. File extension
    3. Fallback to "generic"
    """
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type and _is_media_mime(mime_type):
        return "media"

    if path.suffix.lower() in MEDIA_EXTENSIONS:
        return "media"

    return "generic"


def _is_media_mime(mime_type: str) -> bool:
    return any(mime_type.startswith(prefix) for prefix in MEDIA_MIME_PREFIXES)
