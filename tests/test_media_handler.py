"""
Comprehensive isolated tests for src/telegram/media_handler.py.
"""
import os
import tempfile

import pytest

from src.telegram.media_handler import (
    TelegramMediaHandler,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    AUDIO_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    MIME_MAP,
)


class TestExtensionSets:
    def test_image_extensions(self):
        assert ".png" in IMAGE_EXTENSIONS
        assert ".jpg" in IMAGE_EXTENSIONS
        assert ".jpeg" in IMAGE_EXTENSIONS
        assert ".webp" in IMAGE_EXTENSIONS
        assert ".gif" in IMAGE_EXTENSIONS

    def test_video_extensions(self):
        assert ".mp4" in VIDEO_EXTENSIONS
        assert ".mov" in VIDEO_EXTENSIONS
        assert ".avi" in VIDEO_EXTENSIONS
        assert ".mkv" in VIDEO_EXTENSIONS

    def test_audio_extensions(self):
        assert ".mp3" in AUDIO_EXTENSIONS
        assert ".wav" in AUDIO_EXTENSIONS
        assert ".ogg" in AUDIO_EXTENSIONS
        assert ".m4a" in AUDIO_EXTENSIONS

    def test_document_extensions(self):
        assert ".pdf" in DOCUMENT_EXTENSIONS
        assert ".doc" in DOCUMENT_EXTENSIONS
        assert ".docx" in DOCUMENT_EXTENSIONS
        assert ".txt" in DOCUMENT_EXTENSIONS
        assert ".zip" in DOCUMENT_EXTENSIONS


class TestMimeMap:
    def test_common_mimes(self):
        assert MIME_MAP[".png"] == "image/png"
        assert MIME_MAP[".jpg"] == "image/jpeg"
        assert MIME_MAP[".mp4"] == "video/mp4"
        assert MIME_MAP[".mp3"] == "audio/mpeg"
        assert MIME_MAP[".pdf"] == "application/pdf"


class TestMediaHandlerInit:
    def test_size_constants(self):
        h = TelegramMediaHandler()
        assert h.MAX_PHOTO_SIZE == 10 * 1024 * 1024
        assert h.MAX_DOCUMENT_SIZE == 50 * 1024 * 1024
        assert h.MAX_VIDEO_SIZE == 50 * 1024 * 1024
        assert h.MAX_AUDIO_SIZE == 50 * 1024 * 1024
        assert h.MAX_CAPTION_LENGTH == 1024


class TestDetectType:
    def test_photo_types(self):
        h = TelegramMediaHandler()
        assert h.detect_type("photo.jpg") == "photo"
        assert h.detect_type("image.png") == "photo"
        assert h.detect_type("pic.jpeg") == "photo"
        assert h.detect_type("sticker.webp") == "photo"
        assert h.detect_type("anim.gif") == "photo"

    def test_video_types(self):
        h = TelegramMediaHandler()
        assert h.detect_type("clip.mp4") == "video"
        assert h.detect_type("movie.mov") == "video"
        assert h.detect_type("rec.avi") == "video"
        assert h.detect_type("hd.mkv") == "video"

    def test_audio_types(self):
        h = TelegramMediaHandler()
        assert h.detect_type("song.mp3") == "audio"
        assert h.detect_type("voice.wav") == "audio"
        assert h.detect_type("podcast.ogg") == "audio"
        assert h.detect_type("track.m4a") == "audio"

    def test_document_types(self):
        h = TelegramMediaHandler()
        assert h.detect_type("report.pdf") == "document"
        assert h.detect_type("file.doc") == "document"
        assert h.detect_type("file.docx") == "document"
        assert h.detect_type("readme.txt") == "document"
        assert h.detect_type("archive.zip") == "document"

    def test_unknown_type(self):
        h = TelegramMediaHandler()
        assert h.detect_type("file.xyz") is None
        assert h.detect_type("noextension") is None

    def test_case_insensitive(self):
        h = TelegramMediaHandler()
        assert h.detect_type("PHOTO.JPG") == "photo"
        assert h.detect_type("Video.MP4") == "video"


class TestGetMimeType:
    def test_known_types(self):
        h = TelegramMediaHandler()
        assert h.get_mime_type("test.png") == "image/png"
        assert h.get_mime_type("test.jpg") == "image/jpeg"
        assert h.get_mime_type("test.mp4") == "video/mp4"
        assert h.get_mime_type("test.mp3") == "audio/mpeg"
        assert h.get_mime_type("test.pdf") == "application/pdf"

    def test_unknown_type(self):
        h = TelegramMediaHandler()
        assert h.get_mime_type("test.xyz") == "application/octet-stream"


class TestValidateSize:
    def test_valid_photo(self, tmp_path):
        h = TelegramMediaHandler()
        photo = tmp_path / "photo.jpg"
        photo.write_bytes(b"x" * 1000)
        assert h.validate_size(str(photo), "photo") is True

    def test_oversized_photo(self, tmp_path):
        h = TelegramMediaHandler()
        photo = tmp_path / "photo.jpg"
        photo.write_bytes(b"x" * (10 * 1024 * 1024 + 1))
        assert h.validate_size(str(photo), "photo") is False

    def test_valid_document(self, tmp_path):
        h = TelegramMediaHandler()
        doc = tmp_path / "doc.pdf"
        doc.write_bytes(b"x" * (40 * 1024 * 1024))
        assert h.validate_size(str(doc), "document") is True

    def test_oversized_document(self, tmp_path):
        h = TelegramMediaHandler()
        doc = tmp_path / "doc.pdf"
        doc.write_bytes(b"x" * (50 * 1024 * 1024 + 1))
        assert h.validate_size(str(doc), "document") is False

    def test_unknown_type_uses_document_limit(self, tmp_path):
        h = TelegramMediaHandler()
        f = tmp_path / "file.xyz"
        f.write_bytes(b"x" * 100)
        assert h.validate_size(str(f), "unknown") is True


class TestFormatCaption:
    def test_short_caption(self):
        h = TelegramMediaHandler()
        assert h.format_caption("hello") == "hello"

    def test_exact_length(self):
        h = TelegramMediaHandler()
        caption = "x" * 1024
        assert h.format_caption(caption) == caption

    def test_long_caption_truncated(self):
        h = TelegramMediaHandler()
        caption = "x" * 2000
        result = h.format_caption(caption)
        assert len(result) == 1024
        assert result.endswith("...")

    def test_custom_max_length(self):
        h = TelegramMediaHandler()
        caption = "x" * 100
        result = h.format_caption(caption, 50)
        assert len(result) == 50


class TestGetFileInfo:
    def test_file_info(self, tmp_path):
        h = TelegramMediaHandler()
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"x" * 100)
        info = h.get_file_info(str(f))
        assert info["name"] == "photo.jpg"
        assert info["size"] == 100
        assert info["type"] == "photo"
        assert info["mime"] == "image/jpeg"
        assert info["path"] == str(f)

    def test_file_info_unknown(self, tmp_path):
        h = TelegramMediaHandler()
        f = tmp_path / "data.bin"
        f.write_bytes(b"x" * 10)
        info = h.get_file_info(str(f))
        assert info["name"] == "data.bin"
        assert info["type"] is None
        assert info["mime"] == "application/octet-stream"
