from __future__ import annotations


class FileSplitterError(Exception):
    """Base exception for all file splitter errors."""


class InvalidSizeError(FileSplitterError):
    """Raised when the specified split size is invalid."""


class FFmpegNotFoundError(FileSplitterError):
    """Raised when ffmpeg or ffprobe is not found on the system."""


class CancelledError(FileSplitterError):
    """Raised when a split operation is cancelled by the user."""


class UnsupportedFileError(FileSplitterError):
    """Raised when a file type is not supported for the requested operation."""


class InsufficientSpaceError(FileSplitterError):
    """Raised when there is not enough disk space for the split output."""


class FilePermissionError(FileSplitterError):
    """Raised when a file cannot be read due to permission restrictions."""
