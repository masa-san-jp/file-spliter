from __future__ import annotations

import json

import pytest

from src.core.metadata import PartInfo, SplitMetadata


class TestSplitMetadata:
    def _make_parts(self):
        return (
            PartInfo(index=1, filename="file.part001", size_bytes=1024, sha256="abc"),
            PartInfo(index=2, filename="file.part002", size_bytes=512, sha256="def"),
        )

    def test_create_from_path(self, tmp_path):
        src = tmp_path / "test.txt"
        src.write_bytes(b"hello")
        parts = self._make_parts()

        meta = SplitMetadata.create(src, "sha256abc", "binary", parts)

        assert meta.original_name == "test.txt"
        assert meta.original_ext == ".txt"
        assert meta.original_size_bytes == 5
        assert meta.original_sha256 == "sha256abc"
        assert meta.part_count == 2
        assert meta.split_mode == "binary"

    def test_to_dict_structure(self, tmp_path):
        src = tmp_path / "file.bin"
        src.write_bytes(b"data")
        parts = self._make_parts()
        meta = SplitMetadata.create(src, "hash", "binary", parts)

        d = meta.to_dict()
        assert "original_name" in d
        assert "parts" in d
        assert isinstance(d["parts"], list)
        assert d["parts"][0]["filename"] == "file.part001"

    def test_write_creates_json(self, tmp_path):
        src = tmp_path / "doc.pdf"
        src.write_bytes(b"pdf content")
        parts = self._make_parts()
        meta = SplitMetadata.create(src, "h", "binary", parts)

        out_dir = tmp_path / "output"
        out_dir.mkdir()
        written = meta.write(out_dir)

        assert written.exists()
        loaded = json.loads(written.read_text(encoding="utf-8"))
        assert loaded["original_name"] == "doc.pdf"
        assert len(loaded["parts"]) == 2
