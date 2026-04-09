from __future__ import annotations

import hashlib

import pytest

from src.config.settings import SplitSettings
from src.core.job import SplitJob
from src.splitters.binary_splitter import BinarySplitter


def make_settings(tmp_path, chunk_mb=1):
    return SplitSettings.create(
        chunk_bytes=chunk_mb * 1024 * 1024,
        input_path=tmp_path / "in",
        output_path=tmp_path / "out",
    )


class TestBinarySplitter:
    def test_single_part_small_file(self, tmp_path):
        data = b"hello world"
        src = tmp_path / "in" / "test.txt"
        src.parent.mkdir()
        src.write_bytes(data)

        settings = make_settings(tmp_path)
        job = SplitJob(source_path=src, kind="generic", settings=settings)
        splitter = BinarySplitter()
        out_dir, metadata = splitter.split(job)

        parts = list(out_dir.glob("*.part*"))
        assert len(parts) == 1
        assert metadata.part_count == 1
        assert metadata.original_size_bytes == len(data)

    def test_exact_two_parts(self, tmp_path):
        chunk = 1024 * 1024  # 1 MB
        data = b"A" * chunk + b"B" * chunk
        src = tmp_path / "in" / "two.bin"
        src.parent.mkdir()
        src.write_bytes(data)

        settings = SplitSettings.create(
            chunk_bytes=chunk,
            input_path=tmp_path / "in",
            output_path=tmp_path / "out",
        )
        job = SplitJob(source_path=src, kind="generic", settings=settings)
        splitter = BinarySplitter()
        out_dir, metadata = splitter.split(job)

        assert metadata.part_count == 2

    def test_reassembly_matches_original(self, tmp_path):
        data = b"X" * (2 * 1024 * 1024 + 500)  # 2MB + 500 bytes
        src = tmp_path / "in" / "reassemble.bin"
        src.parent.mkdir()
        src.write_bytes(data)

        settings = SplitSettings.create(
            chunk_bytes=1024 * 1024,
            input_path=tmp_path / "in",
            output_path=tmp_path / "out",
        )
        job = SplitJob(source_path=src, kind="generic", settings=settings)
        splitter = BinarySplitter()
        out_dir, metadata = splitter.split(job)

        parts_sorted = sorted(out_dir.glob("*.part*"))
        reassembled = b"".join(p.read_bytes() for p in parts_sorted)
        assert hashlib.sha256(reassembled).hexdigest() == metadata.original_sha256

    def test_metadata_json_written(self, tmp_path):
        data = b"meta test"
        src = tmp_path / "in" / "meta.bin"
        src.parent.mkdir()
        src.write_bytes(data)

        settings = make_settings(tmp_path)
        job = SplitJob(source_path=src, kind="generic", settings=settings)
        splitter = BinarySplitter()
        out_dir, _ = splitter.split(job)

        assert (out_dir / "metadata.json").exists()

    def test_part_naming(self, tmp_path):
        data = b"Z" * (3 * 1024 * 1024)
        src = tmp_path / "in" / "naming.bin"
        src.parent.mkdir()
        src.write_bytes(data)

        settings = SplitSettings.create(
            chunk_bytes=1024 * 1024,
            input_path=tmp_path / "in",
            output_path=tmp_path / "out",
        )
        job = SplitJob(source_path=src, kind="generic", settings=settings)
        splitter = BinarySplitter()
        out_dir, metadata = splitter.split(job)

        filenames = {p.filename for p in metadata.parts}
        assert "naming.part001" in filenames
        assert "naming.part002" in filenames
        assert "naming.part003" in filenames
