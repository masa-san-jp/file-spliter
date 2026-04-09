from __future__ import annotations

import pytest

from src.config.settings import SplitSettings
from src.services import split_orchestrator


def make_settings(tmp_path, chunk_mb=1):
    return SplitSettings.create(
        chunk_bytes=chunk_mb * 1024 * 1024,
        input_path=tmp_path / "分割前",
        output_path=tmp_path / "分割後",
    )


class TestOrchestrator:
    def test_empty_input_returns_empty(self, tmp_path):
        settings = make_settings(tmp_path)
        (tmp_path / "分割前").mkdir(parents=True)
        results = split_orchestrator.run(settings)
        assert results == []

    def test_missing_input_raises(self, tmp_path):
        from src.utils.errors import FileSplitterError
        settings = make_settings(tmp_path)
        with pytest.raises(FileSplitterError, match="does not exist"):
            split_orchestrator.run(settings)

    def test_generic_file_succeeds(self, tmp_path):
        settings = make_settings(tmp_path)
        in_dir = tmp_path / "分割前"
        in_dir.mkdir()
        (in_dir / "data.bin").write_bytes(b"A" * (2 * 1024 * 1024))

        results = split_orchestrator.run(settings)

        assert len(results) == 1
        assert results[0].success
        assert results[0].metadata is not None
        assert results[0].metadata.part_count == 2

    def test_hidden_files_skipped(self, tmp_path):
        settings = make_settings(tmp_path)
        in_dir = tmp_path / "分割前"
        in_dir.mkdir()
        (in_dir / ".hidden").write_bytes(b"hidden")
        (in_dir / "visible.txt").write_bytes(b"X" * 1024)

        results = split_orchestrator.run(settings)

        assert len(results) == 1
        assert results[0].job.source_path.name == "visible.txt"

    def test_multiple_files_all_processed(self, tmp_path):
        settings = make_settings(tmp_path)
        in_dir = tmp_path / "分割前"
        in_dir.mkdir()

        for name in ("a.txt", "b.bin", "c.pdf"):
            (in_dir / name).write_bytes(b"Z" * 512)

        results = split_orchestrator.run(settings)
        assert len(results) == 3

    def test_cancellation_stops_processing(self, tmp_path):
        from src.services.cancellation import CancellationToken

        settings = make_settings(tmp_path)
        in_dir = tmp_path / "分割前"
        in_dir.mkdir()

        for name in ("a.bin", "b.bin", "c.bin"):
            (in_dir / name).write_bytes(b"X" * (2 * 1024 * 1024))

        token = CancellationToken()
        processed = []

        def on_result(r):
            processed.append(r)
            token.cancel()

        split_orchestrator.run(settings, on_result=on_result, cancel_token=token)

        assert len(processed) <= 2  # cancelled after first or second

    def test_progress_callback_called(self, tmp_path):
        settings = make_settings(tmp_path)
        in_dir = tmp_path / "分割前"
        in_dir.mkdir()
        (in_dir / "prog.bin").write_bytes(b"Y" * 1024)

        calls = []
        split_orchestrator.run(settings, on_progress=lambda name, ratio: calls.append((name, ratio)))

        assert len(calls) > 0
