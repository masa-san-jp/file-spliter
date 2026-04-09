from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ProgressFrame(ttk.LabelFrame):
    """Frame showing current file and overall progress."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, text="進捗", padding=10, **kwargs)
        self._build()

    def _build(self) -> None:
        self._file_label = ttk.Label(self, text="待機中...", anchor=tk.W)
        self._file_label.pack(fill=tk.X, pady=2)

        self._file_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode="determinate")
        self._file_bar.pack(fill=tk.X, pady=2)

        ttk.Label(self, text="全体進捗:", anchor=tk.W).pack(fill=tk.X)

        self._total_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode="determinate")
        self._total_bar.pack(fill=tk.X, pady=2)

        self._total_label = ttk.Label(self, text="0 / 0", anchor=tk.E)
        self._total_label.pack(fill=tk.X)

    def set_file_progress(self, filename: str, ratio: float) -> None:
        self._file_label.config(text=f"処理中: {filename}")
        self._file_bar["value"] = ratio * 100

    def set_total_progress(self, done: int, total: int) -> None:
        self._total_bar["value"] = (done / total * 100) if total else 0
        self._total_label.config(text=f"{done} / {total}")

    def reset(self) -> None:
        self._file_label.config(text="待機中...")
        self._file_bar["value"] = 0
        self._total_bar["value"] = 0
        self._total_label.config(text="0 / 0")
