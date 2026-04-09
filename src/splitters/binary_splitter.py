from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path

from src.config.constants import READ_BUFFER_SIZE
from src.core.hasher import compute_sha256
from src.core.job import SplitJob
from src.core.metadata import PartInfo, SplitMetadata
from src.services.cancellation import CancellationToken
from src.splitters.base_splitter import BaseSplitter, ProgressCallback

logger = logging.getLogger("file_splitter.binary_splitter")


class BinarySplitter(BaseSplitter):
    """Splits generic files into fixed-size byte chunks via streaming I/O."""

    def split(
        self,
        job: SplitJob,
        progress_cb: ProgressCallback | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> tuple[Path, SplitMetadata]:
        source = job.source_path
        chunk_bytes = job.settings.chunk_bytes
        stem = source.stem

        logger.info("Binary split: %s (chunk=%d bytes)", source.name, chunk_bytes)

        original_sha256 = compute_sha256(source, cancel_token)
        total_size = source.stat().st_size
        out_dir = self.prepare_output_dir(job)

        try:
            parts = self._write_parts(
                source, out_dir, stem, chunk_bytes, total_size, progress_cb, cancel_token
            )
            self._verify_integrity(parts, total_size, original_sha256)
        except Exception:
            shutil.rmtree(out_dir, ignore_errors=True)
            raise

        metadata = SplitMetadata.create(
            source_path=source,
            original_sha256=original_sha256,
            split_mode="binary",
            parts=tuple(parts),
        )
        metadata.write(out_dir)

        logger.info("Binary split complete: %d parts -> %s", len(parts), out_dir)
        return out_dir, metadata

    def _write_parts(
        self,
        source: Path,
        out_dir: Path,
        stem: str,
        chunk_bytes: int,
        total_size: int,
        progress_cb: ProgressCallback | None,
        cancel_token: CancellationToken | None,
    ) -> list[PartInfo]:
        parts: list[PartInfo] = []
        bytes_written = 0
        part_index = 1

        with source.open("rb") as src_fh:
            while True:
                if cancel_token:
                    cancel_token.raise_if_cancelled()

                filename = self.part_filename(stem, part_index)
                out_path = out_dir / filename
                size, part_sha256 = self._stream_chunk(
                    src_fh, out_path, chunk_bytes, cancel_token
                )
                if size == 0:
                    out_path.unlink(missing_ok=True)
                    break

                bytes_written += size
                parts.append(
                    PartInfo(index=part_index, filename=filename, size_bytes=size, sha256=part_sha256)
                )
                self.emit_progress(progress_cb, bytes_written / total_size if total_size else 1.0)
                part_index += 1

        return parts

    @staticmethod
    def _stream_chunk(
        src_fh,
        out_path: Path,
        chunk_bytes: int,
        cancel_token: CancellationToken | None,
    ) -> tuple[int, str]:
        """Stream exactly chunk_bytes from src_fh to out_path. Returns (size, sha256)."""
        digest = hashlib.sha256()
        total_written = 0
        remaining = chunk_bytes

        with out_path.open("wb") as dst_fh:
            while remaining > 0:
                if cancel_token:
                    cancel_token.raise_if_cancelled()

                buf = src_fh.read(min(READ_BUFFER_SIZE, remaining))
                if not buf:
                    break

                dst_fh.write(buf)
                digest.update(buf)
                total_written += len(buf)
                remaining -= len(buf)

        return total_written, digest.hexdigest()

    @staticmethod
    def _verify_integrity(parts: list[PartInfo], expected_size: int, original_sha256: str) -> None:
        actual_size = sum(p.size_bytes for p in parts)
        if actual_size != expected_size:
            raise RuntimeError(
                f"Size mismatch: expected {expected_size} bytes, got {actual_size} bytes total."
            )

        combined_digest = hashlib.sha256()
        for part in parts:
            combined_digest.update(bytes.fromhex(part.sha256))

        logger.debug("Size verification passed: %d bytes, original_sha256=%s", actual_size, original_sha256)
