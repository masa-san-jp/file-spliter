from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

from src.core.job import SplitJob
from src.core.metadata import SplitMetadata
from src.services.cancellation import CancellationToken
from src.utils.paths import ensure_dir, unique_output_subdir

logger = logging.getLogger("file_splitter.splitter")

ProgressCallback = Callable[[float], None]  # 0.0–1.0


class BaseSplitter(ABC):
    """Abstract base class for all file splitters."""

    @abstractmethod
    def split(
        self,
        job: SplitJob,
        progress_cb: ProgressCallback | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> tuple[Path, SplitMetadata]:
        """
        Execute the split operation.

        Returns:
            Tuple of (output_directory, metadata).
        """
        ...

    def prepare_output_dir(self, job: SplitJob) -> Path:
        """Create and return a unique output subdirectory for the job."""
        stem = job.source_path.stem
        sub = unique_output_subdir(job.settings.output_path, stem)
        return ensure_dir(sub)

    @staticmethod
    def part_filename(stem: str, index: int, ext: str = "") -> str:
        """Generate a part filename like 'name.part001' or 'name_001.mp3'."""
        if ext:
            return f"{stem}_{index:03d}{ext}"
        return f"{stem}.part{index:03d}"

    @staticmethod
    def emit_progress(
        progress_cb: ProgressCallback | None, value: float
    ) -> None:
        if progress_cb is not None:
            progress_cb(max(0.0, min(1.0, value)))
