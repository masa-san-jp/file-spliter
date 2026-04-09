from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class PartInfo:
    index: int
    filename: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class SplitMetadata:
    original_name: str
    original_ext: str
    original_size_bytes: int
    original_sha256: str
    split_mode: str
    created_at: str
    part_count: int
    parts: tuple[PartInfo, ...]

    @staticmethod
    def create(
        source_path: Path,
        original_sha256: str,
        split_mode: str,
        parts: tuple[PartInfo, ...],
    ) -> "SplitMetadata":
        return SplitMetadata(
            original_name=source_path.name,
            original_ext=source_path.suffix,
            original_size_bytes=source_path.stat().st_size,
            original_sha256=original_sha256,
            split_mode=split_mode,
            created_at=datetime.now(timezone.utc).isoformat(),
            part_count=len(parts),
            parts=parts,
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["parts"] = [asdict(p) for p in self.parts]
        return data

    def write(self, output_dir: Path) -> Path:
        """Write metadata as JSON into output_dir. Returns the written path."""
        meta_path = output_dir / "metadata.json"
        meta_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return meta_path
