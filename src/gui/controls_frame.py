from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class ControlsFrame(ttk.LabelFrame):
    """Frame containing split settings and action buttons."""

    def __init__(
        self,
        parent: tk.Widget,
        on_start: Callable[[], None],
        on_cancel: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(parent, text="設定", padding=10, **kwargs)
        self._on_start = on_start
        self._on_cancel = on_cancel
        self._build()

    def _build(self) -> None:
        # Size input row
        size_row = ttk.Frame(self)
        size_row.pack(fill=tk.X, pady=4)

        ttk.Label(size_row, text="分割サイズ:").pack(side=tk.LEFT)

        self._size_var = tk.StringVar(value="100")
        self._size_entry = ttk.Entry(size_row, textvariable=self._size_var, width=10)
        self._size_entry.pack(side=tk.LEFT, padx=4)

        self._unit_var = tk.StringVar(value="MB")
        unit_combo = ttk.Combobox(
            size_row,
            textvariable=self._unit_var,
            values=["KB", "MB", "GB"],
            width=5,
            state="readonly",
        )
        unit_combo.pack(side=tk.LEFT)

        # Media mode row
        mode_row = ttk.Frame(self)
        mode_row.pack(fill=tk.X, pady=4)

        ttk.Label(mode_row, text="音声/動画モード:").pack(side=tk.LEFT)

        self._mode_var = tk.StringVar(value="fast")
        ttk.Radiobutton(
            mode_row, text="高速モード", variable=self._mode_var, value="fast"
        ).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(
            mode_row, text="精度優先モード", variable=self._mode_var, value="accurate"
        ).pack(side=tk.LEFT)

        # Buttons row
        btn_row = ttk.Frame(self)
        btn_row.pack(fill=tk.X, pady=6)

        self._start_btn = ttk.Button(
            btn_row, text="実行", command=self._on_start
        )
        self._start_btn.pack(side=tk.LEFT, padx=4)

        self._cancel_btn = ttk.Button(
            btn_row, text="中断", command=self._on_cancel, state=tk.DISABLED
        )
        self._cancel_btn.pack(side=tk.LEFT)

    @property
    def size_value(self) -> str:
        return self._size_var.get().strip()

    @property
    def unit(self) -> str:
        return self._unit_var.get()

    @property
    def media_mode(self) -> str:
        return self._mode_var.get()

    def set_running(self, running: bool) -> None:
        if running:
            self._start_btn.config(state=tk.DISABLED)
            self._cancel_btn.config(state=tk.NORMAL)
            self._size_entry.config(state=tk.DISABLED)
        else:
            self._start_btn.config(state=tk.NORMAL)
            self._cancel_btn.config(state=tk.DISABLED)
            self._size_entry.config(state=tk.NORMAL)
