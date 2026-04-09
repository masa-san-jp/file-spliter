from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.core.file_detector import detect_kind


class TestDetectKind:
    def test_mp3_by_extension(self):
        assert detect_kind(Path("audio.mp3")) == "media"

    def test_mp4_by_extension(self):
        assert detect_kind(Path("video.mp4")) == "media"

    def test_wav_by_extension(self):
        assert detect_kind(Path("audio.wav")) == "media"

    def test_mkv_by_extension(self):
        assert detect_kind(Path("video.mkv")) == "media"

    def test_pdf_is_generic(self):
        assert detect_kind(Path("document.pdf")) == "generic"

    def test_zip_is_generic(self):
        assert detect_kind(Path("archive.zip")) == "generic"

    def test_txt_is_generic(self):
        assert detect_kind(Path("notes.txt")) == "generic"

    def test_unknown_extension_is_generic(self):
        assert detect_kind(Path("data.xyz123")) == "generic"

    def test_mime_type_audio_overrides(self):
        with patch("mimetypes.guess_type", return_value=("audio/mpeg", None)):
            assert detect_kind(Path("file.unknown")) == "media"

    def test_mime_type_video_overrides(self):
        with patch("mimetypes.guess_type", return_value=("video/mp4", None)):
            assert detect_kind(Path("file.unknown")) == "media"

    def test_mime_type_text_is_generic(self):
        with patch("mimetypes.guess_type", return_value=("text/plain", None)):
            assert detect_kind(Path("file.txt")) == "generic"

    def test_uppercase_extension(self):
        assert detect_kind(Path("audio.MP3")) == "media"
