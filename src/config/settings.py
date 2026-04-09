from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.utils.paths import input_dir, output_dir


@dataclass(frozen=True)
class SplitSettings:
    chunk_bytes: int
    media_mode: Literal["fast", "accurate"]
    input_path: Path
    output_path: Path

    @staticmethod
    def create(
        chunk_bytes: int,
        media_mode: Literal["fast", "accurate"] = "fast",
        input_path: Path | None = None,
        output_path: Path | None = None,
    ) -> "SplitSettings":
        return SplitSettings(
            chunk_bytes=chunk_bytes,
            media_mode=media_mode,
            input_path=input_path or input_dir(),
            output_path=output_path or output_dir(),
        )
