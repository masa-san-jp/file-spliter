from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.settings import SplitSettings
from src.core.job import SplitJob
from src.splitters.media_splitter import MediaSplitter


def make_settings(tmp_path, chunk_mb=10, mode="fast"):
    return SplitSettings.create(
        chunk_bytes=chunk_mb * 1024 * 1024,
        media_mode=mode,
        input_path=tmp_path / "in",
        output_path=tmp_path / "out",
    )


def write_fake_segments(out_dir: Path, stem: str, ext: str, count: int = 2) -> None:
    """Simulate ffmpeg writing segment files (uses _ffmpeg_ prefix pattern)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (out_dir / f"{stem}_ffmpeg_{i:03d}{ext}").write_bytes(b"fake_media_data" * 1000)


def _extract_output_dir(args: list[str]) -> Path:
    """Parse the ffmpeg output pattern arg (last arg, may have file: prefix)."""
    raw = args[-1]
    # Strip optional file: prefix
    if raw.startswith("file:"):
        raw = raw[len("file:"):]
    return Path(raw).parent


class TestMediaSplitter:
    @patch("src.services.ffmpeg_runner.ensure_available")
    @patch("src.services.ffmpeg_runner.get_duration_seconds", return_value=60.0)
    @patch("src.services.ffmpeg_runner.run_ffmpeg")
    def test_fast_mode_produces_metadata(self, mock_run, mock_dur, mock_check, tmp_path):
        src = tmp_path / "in" / "audio.mp3"
        src.parent.mkdir()
        src.write_bytes(b"fake_mp3" * 10000)

        settings = make_settings(tmp_path)
        job = SplitJob(source_path=src, kind="media", settings=settings)
        splitter = MediaSplitter()

        def fake_ffmpeg(args, **kwargs):
            write_fake_segments(_extract_output_dir(args), src.stem, ".mp3", count=2)

        mock_run.side_effect = fake_ffmpeg

        out_dir, metadata = splitter.split(job)

        assert metadata.part_count == 2
        assert metadata.split_mode == "media_fast"
        assert (out_dir / "metadata.json").exists()

    @patch("src.services.ffmpeg_runner.ensure_available")
    @patch("src.services.ffmpeg_runner.get_stream_info", return_value={"has_video": True, "has_audio": True})
    @patch("src.services.ffmpeg_runner.get_duration_seconds", return_value=120.0)
    @patch("src.services.ffmpeg_runner.run_ffmpeg")
    def test_accurate_mode(self, mock_run, mock_dur, mock_stream, mock_check, tmp_path):
        src = tmp_path / "in" / "video.mp4"
        src.parent.mkdir()
        src.write_bytes(b"fake_mp4" * 10000)

        settings = make_settings(tmp_path, mode="accurate")
        job = SplitJob(source_path=src, kind="media", settings=settings)
        splitter = MediaSplitter()

        def fake_ffmpeg(args, **kwargs):
            write_fake_segments(_extract_output_dir(args), src.stem, ".mp4", count=3)

        mock_run.side_effect = fake_ffmpeg

        out_dir, metadata = splitter.split(job)

        assert metadata.split_mode == "media_accurate"
        assert metadata.part_count == 3

    @patch("src.services.ffmpeg_runner.ensure_available")
    @patch("src.services.ffmpeg_runner.get_duration_seconds", return_value=60.0)
    @patch("src.services.ffmpeg_runner.run_ffmpeg")
    def test_parts_renamed_correctly(self, mock_run, mock_dur, mock_check, tmp_path):
        src = tmp_path / "in" / "song.mp3"
        src.parent.mkdir()
        src.write_bytes(b"x" * 10000)

        settings = make_settings(tmp_path)
        job = SplitJob(source_path=src, kind="media", settings=settings)
        splitter = MediaSplitter()

        def fake_ffmpeg(args, **kwargs):
            write_fake_segments(_extract_output_dir(args), "song", ".mp3", count=2)

        mock_run.side_effect = fake_ffmpeg

        out_dir, metadata = splitter.split(job)
        filenames = {p.filename for p in metadata.parts}
        assert "song_001.mp3" in filenames
        assert "song_002.mp3" in filenames

    @patch("src.services.ffmpeg_runner.ensure_available")
    @patch("src.services.ffmpeg_runner.get_stream_info", return_value={"has_video": False, "has_audio": True})
    @patch("src.services.ffmpeg_runner.get_duration_seconds", return_value=90.0)
    @patch("src.services.ffmpeg_runner.run_ffmpeg")
    def test_accurate_mode_audio_only(self, mock_run, mock_dur, mock_stream, mock_check, tmp_path):
        """Audio-only files in accurate mode should not use video codec args."""
        src = tmp_path / "in" / "music.mp3"
        src.parent.mkdir()
        src.write_bytes(b"audio" * 10000)

        settings = make_settings(tmp_path, mode="accurate")
        job = SplitJob(source_path=src, kind="media", settings=settings)
        splitter = MediaSplitter()

        captured_args: list[list[str]] = []

        def fake_ffmpeg(args, **kwargs):
            captured_args.append(args)
            write_fake_segments(_extract_output_dir(args), "music", ".mp3", count=2)

        mock_run.side_effect = fake_ffmpeg

        out_dir, metadata = splitter.split(job)

        # libx264 should NOT appear in audio-only mode
        flat_args = " ".join(captured_args[0])
        assert "libx264" not in flat_args
        assert metadata.part_count == 2
