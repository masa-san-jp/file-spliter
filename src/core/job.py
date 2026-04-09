from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.config.settings import SplitSettings
from src.core.metadata import SplitMetadata


FileKind = Literal["media", "generic"]


@dataclass(frozen=True)
class SplitJob:
    source_path: Path
    kind: FileKind
    settings: SplitSettings


@dataclass(frozen=True)
class SplitResult:
    job: SplitJob
    success: bool
    output_dir: Path | None
    metadata: SplitMetadata | None
    error_message: str | None
    warnings: tuple[str, ...]

    @staticmethod
    def ok(
        job: SplitJob,
        output_dir: Path,
        metadata: SplitMetadata,
        warnings: tuple[str, ...] = (),
    ) -> "SplitResult":
        return SplitResult(
            job=job,
            success=True,
            output_dir=output_dir,
            metadata=metadata,
            error_message=None,
            warnings=warnings,
        )

    @staticmethod
    def fail(job: SplitJob, error_message: str) -> "SplitResult":
        return SplitResult(
            job=job,
            success=False,
            output_dir=None,
            metadata=None,
            error_message=error_message,
            warnings=(),
        )
