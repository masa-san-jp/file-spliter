from __future__ import annotations

import queue
import tkinter as tk
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class GuiMessage:
    kind: str  # "progress" | "result" | "total" | "done" | "error" | "log"
    payload: Any


class GuiBridge:
    """
    Thread-safe bridge between the worker thread and the Tk event loop.
    Uses queue.Queue for message passing and tk.after() for periodic polling.
    Exactly one `after` callback is pending at any time while active.
    """

    POLL_INTERVAL_MS = 50

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._queue: queue.Queue[GuiMessage] = queue.Queue()
        self._handlers: dict[str, Callable[[Any], None]] = {}
        self._after_id: str | None = None
        self._active = False

    def register(self, kind: str, handler: Callable[[Any], None]) -> None:
        self._handlers[kind] = handler

    def post(self, kind: str, payload: Any = None) -> None:
        """Thread-safe: post a message from any thread."""
        self._queue.put(GuiMessage(kind=kind, payload=payload))

    def start_polling(self) -> None:
        """Start the polling loop. Safe to call when already active."""
        if not self._active:
            self._active = True
            self._schedule_poll()

    def stop_polling(self) -> None:
        """Stop the polling loop and drain any remaining messages synchronously."""
        self._active = False
        if self._after_id is not None:
            self._root.after_cancel(self._after_id)
            self._after_id = None
        self._drain()

    def _schedule_poll(self) -> None:
        self._after_id = self._root.after(self.POLL_INTERVAL_MS, self._poll)

    def _poll(self) -> None:
        self._after_id = None
        self._drain()
        if self._active:
            self._schedule_poll()

    def _drain(self) -> None:
        while True:
            try:
                msg = self._queue.get_nowait()
            except queue.Empty:
                break
            handler = self._handlers.get(msg.kind)
            if handler:
                handler(msg.payload)
