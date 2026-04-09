from __future__ import annotations

from src.core.job import FileKind
from src.splitters.base_splitter import BaseSplitter
from src.splitters.binary_splitter import BinarySplitter
from src.splitters.media_splitter import MediaSplitter


def create(kind: FileKind) -> BaseSplitter:
    """Return the appropriate splitter for the given file kind."""
    if kind == "media":
        return MediaSplitter()
    return BinarySplitter()
