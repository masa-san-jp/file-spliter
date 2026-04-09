from __future__ import annotations

import threading

from src.utils.errors import CancelledError


class CancellationToken:
    """Thread-safe cancellation token backed by a threading.Event."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        """Signal cancellation."""
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        """Raise CancelledError if cancellation has been requested."""
        if self._event.is_set():
            raise CancelledError("Operation was cancelled by the user.")
