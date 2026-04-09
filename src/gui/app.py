from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from src.gui.main_window import MainWindow
from src.services.logger_setup import setup_logger
from src.utils.paths import ensure_dir, input_dir, output_dir


def run() -> None:
    """Initialize and launch the tkinter application."""
    setup_logger()

    ensure_dir(input_dir())
    ensure_dir(output_dir())

    root = tk.Tk()
    root.title("ファイル分割プログラム")
    root.geometry("900x650")
    root.minsize(700, 500)

    try:
        _apply_theme(root)
    except Exception:
        pass  # theme not critical

    MainWindow(root)
    root.mainloop()


def _apply_theme(root: tk.Tk) -> None:
    style = tk.ttk.Style(root)
    available = style.theme_names()
    preferred = ("aqua", "clam", "alt", "default")
    for theme in preferred:
        if theme in available:
            style.theme_use(theme)
            break
