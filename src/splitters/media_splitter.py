from __future__ import annotations

import logging
import shutil
from pathlib import Path

from src.config.constants import MEDIA_SIZE_TOLERANCE_RATIO
from src.core.hasher import compute_sha256
from src.core.job import SplitJob
from src.core.metadata import PartInfo, SplitMetadata
from src.services import ffmpeg_runner
from src.services.cancellation import CancellationToken
from src.splitters.base_splitter import BaseSplitter, ProgressCallback

logger = logging.getLogger("file_splitter.media_splitter")


class MediaSplitter(BaseSplitter):
    """Splits audio/video files using ffmpeg to produce playable segments."""

    def split(
        self,
        job: SplitJob,
        progress_cb: ProgressCallback | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> tuple[Path, SplitMetadata]:
        ffmpeg_runner.ensure_available()

        source = job.source_path
        mode = job.settings.media_mode
        chunk_bytes = job.settings.chunk_bytes

        logger.info("Media split: %s (mode=%s, chunk=%d)", source.name, mode, chunk_bytes)

        original_sha256 = compute_sha256(source, cancel_token)
        out_dir = self.prepare_output_dir(job)

        try:
            parts, warnings = self._do_split(
                source, out_dir, mode, chunk_bytes, progress_cb, cancel_token
            )
        except Exception:
            shutil.rmtree(out_dir, ignore_errors=True)
            raise

        metadata = SplitMetadata.create(
            source_path=source,
            original_sha256=original_sha256,
            split_mode=f"media_{mode}",
            parts=tuple(parts),
        )
        metadata.write(out_dir)

        logger.info("Media split complete: %d parts -> %s", len(parts), out_dir)
        return out_dir, metadata

    def _do_split(
        self,
        source: Path,
        out_dir: Path,
        mode: str,
        chunk_bytes: int,
        progress_cb: ProgressCallback | None,
        cancel_token: CancellationToken | None,
    ) -> tuple[list[PartInfo], list[str]]:
        segment_seconds = self._estimate_segment_seconds(source, chunk_bytes)
        ext = source.suffix.lower()
        stem = source.stem
        warnings: list[str] = []

        if mode == "fast":
            self._run_fast(source, out_dir, stem, ext, segment_seconds, cancel_token)
        else:
            stream_info = ffmpeg_runner.get_stream_info(source)
            self._run_accurate(source, out_dir, stem, ext, segment_seconds, chunk_bytes, stream_info, cancel_token)

        parts = self._collect_and_rename_parts(out_dir, stem, ext, source.stat().st_size, warnings)
        return parts, warnings

    def _run_fast(
        self,
        source: Path,
        out_dir: Path,
        stem: str,
        ext: str,
        segment_seconds: float,
        cancel_token: CancellationToken | None,
    ) -> None:
        pattern = str(out_dir / f"{stem}_ffmpeg_%03d{ext}")
        args = [
            "-i", f"file:{source.resolve()}",
            "-c", "copy",
            "-f", "segment",
            "-segment_time", str(int(segment_seconds)),
            "-reset_timestamps", "1",
            f"file:{pattern}",
        ]
        ffmpeg_runner.run_ffmpeg(args, cancel_token=cancel_token)

    def _run_accurate(
        self,
        source: Path,
        out_dir: Path,
        stem: str,
        ext: str,
        segment_seconds: float,
        chunk_bytes: int,
        stream_info: dict[str, bool],
        cancel_token: CancellationToken | None,
    ) -> None:
        target_bitrate = self._target_bitrate_kbps(chunk_bytes, segment_seconds)
        pattern = str(out_dir / f"{stem}_ffmpeg_%03d{ext}")
        force_kf = f"expr:gte(t,n_forced*{int(segment_seconds)})"

        if stream_info.get("has_video"):
            codec_args = [
                "-c:v", "libx264",
                "-b:v", f"{max(64, target_bitrate - 128)}k",
                "-force_key_frames", force_kf,
                "-c:a", "aac",
                "-b:a", "128k",
            ]
        else:
            codec_args = ["-c:a", "aac", "-b:a", f"{min(target_bitrate, 320)}k"]

        args = [
            "-i", f"file:{source.resolve()}",
            *codec_args,
            "-f", "segment",
            "-segment_time", str(int(segment_seconds)),
            "-reset_timestamps", "1",
            f"file:{pattern}",
        ]
        ffmpeg_runner.run_ffmpeg(args, cancel_token=cancel_token)

    def _collect_and_rename_parts(
        self,
        out_dir: Path,
        stem: str,
        ext: str,
        original_size: int,
        warnings: list[str],
    ) -> list[PartInfo]:
        ffmpeg_files = sorted(out_dir.glob(f"{stem}_ffmpeg_*{ext}"))
        if not ffmpeg_files:
            raise RuntimeError(f"No output segments found in {out_dir}")

        # Two-pass rename: ffmpeg_NNN -> tmp_NNN, then tmp_NNN -> final name
        tmp_files: list[Path] = []
        for f in ffmpeg_files:
            tmp = f.with_name(f"_tmp_{f.name}")
            f.rename(tmp)
            tmp_files.append(tmp)

        parts: list[PartInfo] = []
        for i, tmp in enumerate(tmp_files, start=1):
            final_name = self.part_filename(stem, i, ext)
            final_path = out_dir / final_name
            tmp.rename(final_path)
            size = final_path.stat().st_size
            sha = compute_sha256(final_path)
            parts.append(PartInfo(index=i, filename=final_name, size_bytes=size, sha256=sha))

        self._check_size_tolerance(parts, original_size, warnings)
        return parts

    @staticmethod
    def _estimate_segment_seconds(source: Path, chunk_bytes: int) -> float:
        duration = ffmpeg_runner.get_duration_seconds(source)
        file_size = source.stat().st_size
        if file_size == 0 or duration == 0:
            return 60.0
        bytes_per_second = file_size / duration
        return max(1.0, chunk_bytes / bytes_per_second)

    @staticmethod
    def _target_bitrate_kbps(chunk_bytes: int, segment_seconds: float) -> int:
        if segment_seconds <= 0:
            return 512
        bits = chunk_bytes * 8
        return int(bits / segment_seconds / 1000)

    @staticmethod
    def _check_size_tolerance(
        parts: list[PartInfo],
        original_size: int,
        warnings: list[str],
    ) -> None:
        if not parts:
            return
        chunk_target = original_size / len(parts)
        for part in parts:
            ratio = (part.size_bytes - chunk_target) / chunk_target
            if ratio > MEDIA_SIZE_TOLERANCE_RATIO:
                msg = (
                    f"{part.filename}: size {part.size_bytes:,} bytes exceeds "
                    f"target by {ratio:.1%} (tolerance {MEDIA_SIZE_TOLERANCE_RATIO:.0%})"
                )
                warnings.append(msg)
                logger.warning(msg)
