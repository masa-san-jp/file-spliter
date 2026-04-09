from __future__ import annotations

import hashlib

import pytest

from src.core.hasher import compute_sha256
from src.services.cancellation import CancellationToken
from src.utils.errors import CancelledError


class TestComputeSha256:
    def test_known_hash(self, tmp_path):
        data = b"hello world"
        f = tmp_path / "test.bin"
        f.write_bytes(data)

        expected = hashlib.sha256(data).hexdigest()
        assert compute_sha256(f) == expected

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert compute_sha256(f) == expected

    def test_large_file(self, tmp_path):
        data = b"x" * (3 * 1024 * 1024)  # 3 MB
        f = tmp_path / "large.bin"
        f.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert compute_sha256(f) == expected

    def test_cancellation_raises(self, tmp_path):
        data = b"some data"
        f = tmp_path / "test.bin"
        f.write_bytes(data)
        token = CancellationToken()
        token.cancel()
        with pytest.raises(CancelledError):
            compute_sha256(f, token)
