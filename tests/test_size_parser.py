from __future__ import annotations

import pytest

from src.core.size_parser import format_size, parse_size
from src.utils.errors import InvalidSizeError


class TestParseSize:
    def test_mb_basic(self):
        assert parse_size("100", "MB") == 100 * 1024 * 1024

    def test_kb_basic(self):
        assert parse_size("2048", "KB") == 2048 * 1024

    def test_gb_basic(self):
        assert parse_size("1", "GB") == 1024 * 1024 * 1024

    def test_fractional(self):
        assert parse_size("1.5", "GB") == int(1.5 * 1024 * 1024 * 1024)

    def test_minimum_valid(self):
        # exactly 1 MB
        assert parse_size("1", "MB") == 1024 * 1024

    def test_maximum_valid(self):
        # exactly 10 GB
        assert parse_size("10", "GB") == 10 * 1024 * 1024 * 1024

    def test_below_minimum_raises(self):
        with pytest.raises(InvalidSizeError, match="minimum"):
            parse_size("0.5", "MB")

    def test_above_maximum_raises(self):
        with pytest.raises(InvalidSizeError, match="maximum"):
            parse_size("11", "GB")

    def test_zero_raises(self):
        with pytest.raises(InvalidSizeError, match="positive"):
            parse_size("0", "MB")

    def test_negative_raises(self):
        with pytest.raises(InvalidSizeError, match="positive"):
            parse_size("-1", "MB")

    def test_non_numeric_raises(self):
        with pytest.raises(InvalidSizeError, match="Invalid size value"):
            parse_size("abc", "MB")

    def test_unknown_unit_raises(self):
        with pytest.raises(InvalidSizeError, match="Unknown unit"):
            parse_size("100", "TB")


class TestFormatSize:
    def test_bytes(self):
        assert "B" in format_size(512)

    def test_kilobytes(self):
        assert "KB" in format_size(2048)

    def test_megabytes(self):
        assert "MB" in format_size(5 * 1024 * 1024)

    def test_gigabytes(self):
        assert "GB" in format_size(2 * 1024 * 1024 * 1024)
