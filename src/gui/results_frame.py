from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from src.core.job import SplitResult
from src.core.size_parser import format_size


class ResultsFrame(ttk.LabelFrame):
    """Frame displaying the split results in a table."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, text="結果", padding=10, **kwargs)
        self._build()

    def _build(self) -> None:
        columns = ("status", "filename", "original_size", "parts", "output", "warnings")
        self._tree = ttk.Treeview(self, columns=columns, show="headings", height=8)

        headers = {
            "status": ("状態", 60),
            "filename": ("ファイル名", 180),
            "original_size": ("元サイズ", 80),
            "parts": ("断片数", 60),
            "output": ("出力先", 200),
            "warnings": ("警告", 60),
        }
        for col, (text, width) in headers.items():
            self._tree.heading(col, text=text)
            self._tree.column(col, width=width, anchor=tk.CENTER if col in ("status", "parts", "warnings") else tk.W)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Summary row
        summary_row = ttk.Frame(self)
        summary_row.pack(fill=tk.X, pady=4)

        self._summary_label = ttk.Label(summary_row, text="")
        self._summary_label.pack(side=tk.LEFT)

        self._open_btn = ttk.Button(
            summary_row, text="出力先を開く", command=self._open_output_dir, state=tk.DISABLED
        )
        self._open_btn.pack(side=tk.RIGHT)

        self._output_dir: Path | None = None

    def clear(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._summary_label.config(text="")
        self._open_btn.config(state=tk.DISABLED)
        self._output_dir = None

    def add_result(self, result: SplitResult) -> None:
        status = "成功" if result.success else "失敗"
        filename = result.job.source_path.name
        orig_size = format_size(result.job.source_path.stat().st_size) if result.job.source_path.exists() else "-"
        parts = str(result.metadata.part_count) if result.metadata else "-"
        output = str(result.output_dir) if result.output_dir else (result.error_message or "-")
        warnings = str(len(result.warnings)) if result.warnings else "0"

        tag = "success" if result.success else "failure"
        self._tree.insert("", tk.END, values=(status, filename, orig_size, parts, output, warnings), tags=(tag,))
        self._tree.tag_configure("success", foreground="green")
        self._tree.tag_configure("failure", foreground="red")

        if result.output_dir and self._output_dir is None:
            self._output_dir = result.output_dir.parent
            self._open_btn.config(state=tk.NORMAL)

    def set_summary(self, success: int, failure: int, warnings: int) -> None:
        self._summary_label.config(
            text=f"成功: {success}  失敗: {failure}  警告あり: {warnings}"
        )

    def _open_output_dir(self) -> None:
        if self._output_dir and self._output_dir.exists():
            if sys.platform == "darwin":
                subprocess.run(["open", str(self._output_dir)], check=False)
            elif sys.platform == "win32":
                subprocess.run(["explorer", str(self._output_dir)], check=False)
            else:
                subprocess.run(["xdg-open", str(self._output_dir)], check=False)
