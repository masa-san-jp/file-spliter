from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from src.config.settings import SplitSettings
from src.core.job import SplitResult
from src.core.size_parser import parse_size
from src.gui.controls_frame import ControlsFrame
from src.gui.gui_bridge import GuiBridge
from src.gui.progress_frame import ProgressFrame
from src.gui.results_frame import ResultsFrame
from src.services import split_orchestrator
from src.services.cancellation import CancellationToken
from src.utils.errors import InvalidSizeError
from src.utils.paths import input_dir, output_dir

logger = logging.getLogger("file_splitter.main_window")


class MainWindow(ttk.Frame):
    """Main application window assembled from sub-frames."""

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=12)
        self._root = root
        self._cancel_token: CancellationToken | None = None
        self._worker_thread: threading.Thread | None = None
        self._done_files = 0
        self._total_files = 0
        self._bridge = GuiBridge(root)
        self._build()
        self._wire_bridge()
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        self.pack(fill=tk.BOTH, expand=True)

        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, pady=4)
        ttk.Label(info_frame, text=f"入力: {input_dir()}").pack(side=tk.LEFT)
        ttk.Label(info_frame, text=f"  出力: {output_dir()}").pack(side=tk.LEFT)

        self._controls = ControlsFrame(
            self, on_start=self._on_start, on_cancel=self._on_cancel
        )
        self._controls.pack(fill=tk.X, pady=4)

        self._progress = ProgressFrame(self)
        self._progress.pack(fill=tk.X, pady=4)

        self._results = ResultsFrame(self)
        self._results.pack(fill=tk.BOTH, expand=True, pady=4)

        log_frame = ttk.LabelFrame(self, text="ログ", padding=6)
        log_frame.pack(fill=tk.X)
        self._log_text = tk.Text(log_frame, height=5, state=tk.DISABLED, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_scroll.set)
        self._log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _wire_bridge(self) -> None:
        self._bridge.register("total", self._handle_total)
        self._bridge.register("progress", self._handle_progress)
        self._bridge.register("result", self._handle_result)
        self._bridge.register("done", self._handle_done)
        self._bridge.register("error", self._handle_error)
        self._bridge.register("log", self._handle_log)

    def _on_start(self) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            return  # Prevent double-start

        try:
            chunk_bytes = parse_size(self._controls.size_value, self._controls.unit)
        except InvalidSizeError as exc:
            messagebox.showerror("入力エラー", str(exc))
            return

        self._results.clear()
        self._progress.reset()
        self._done_files = 0
        self._total_files = 0

        settings = SplitSettings.create(
            chunk_bytes=chunk_bytes,
            media_mode=self._controls.media_mode,  # type: ignore[arg-type]
        )

        self._cancel_token = CancellationToken()
        self._controls.set_running(True)
        self._bridge.start_polling()

        self._worker_thread = threading.Thread(
            target=self._run_worker, args=(settings,), daemon=True
        )
        self._worker_thread.start()

    def _on_cancel(self) -> None:
        if self._cancel_token:
            self._cancel_token.cancel()
            self._append_log("中断リクエストを送信しました...")

    def _on_close(self) -> None:
        if self._cancel_token:
            self._cancel_token.cancel()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=3)
        self._root.destroy()

    def _run_worker(self, settings: SplitSettings) -> None:
        try:
            split_orchestrator.run(
                settings=settings,
                on_file_count=lambda n: self._bridge.post("total", n),
                on_progress=lambda name, ratio: self._bridge.post(
                    "progress", {"name": name, "ratio": ratio}
                ),
                on_result=lambda r: self._bridge.post("result", r),
                cancel_token=self._cancel_token,
            )
            self._bridge.post("done", None)

        except Exception as exc:
            logger.exception("Worker thread error")
            self._bridge.post("error", str(exc))

    def _handle_total(self, total: int) -> None:
        self._total_files = total
        if total == 0:
            self._append_log("処理対象ファイルが見つかりません。")

    def _handle_progress(self, payload: dict) -> None:
        self._progress.set_file_progress(payload["name"], payload["ratio"])

    def _handle_result(self, result: SplitResult) -> None:
        self._done_files += 1
        self._results.add_result(result)
        self._progress.set_total_progress(self._done_files, self._total_files)
        status = "成功" if result.success else "失敗"
        self._append_log(f"[{status}] {result.job.source_path.name}")

    def _handle_done(self, _payload) -> None:
        self._controls.set_running(False)
        self._bridge.stop_polling()
        self._append_log(f"完了: {self._done_files} 件処理しました")

    def _handle_error(self, message: str) -> None:
        self._controls.set_running(False)
        self._bridge.stop_polling()
        messagebox.showerror("エラー", message)

    def _handle_log(self, message: str) -> None:
        self._append_log(message)

    def _append_log(self, message: str) -> None:
        self._log_text.config(state=tk.NORMAL)
        self._log_text.insert(tk.END, message + "\n")
        self._log_text.see(tk.END)
        self._log_text.config(state=tk.DISABLED)
