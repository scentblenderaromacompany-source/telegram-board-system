"""
Telegram media handling utilities.
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".zip"}

MIME_MAP = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif", ".mp4": "video/mp4",
    ".mov": "video/quicktime", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".ogg": "audio/ogg", ".pdf": "application/pdf",
}


class TelegramMediaHandler:
    """
    Handles Telegram media operations:
    - File type detection
    - Size validation
    - Caption formatting
    """

    MAX_PHOTO_SIZE = 10 * 1024 * 1024
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024
    MAX_VIDEO_SIZE = 50 * 1024 * 1024
    MAX_AUDIO_SIZE = 50 * 1024 * 1024
    MAX_CAPTION_LENGTH = 1024

    def detect_type(self, file_path: str) -> Optional[str]:
        ext = Path(file_path).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            return "photo"
        elif ext in VIDEO_EXTENSIONS:
            return "video"
        elif ext in AUDIO_EXTENSIONS:
            return "audio"
        elif ext in DOCUMENT_EXTENSIONS:
            return "document"
        return None

    def get_mime_type(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        return MIME_MAP.get(ext, "application/octet-stream")

    def validate_size(self, file_path: str, media_type: str) -> bool:
        size = os.path.getsize(file_path)
        limits = {
            "photo": self.MAX_PHOTO_SIZE,
            "video": self.MAX_VIDEO_SIZE,
            "audio": self.MAX_AUDIO_SIZE,
            "document": self.MAX_DOCUMENT_SIZE,
        }
        return size <= limits.get(media_type, self.MAX_DOCUMENT_SIZE)

    def format_caption(self, caption: str, max_length: int = None) -> str:
        max_len = max_length or self.MAX_CAPTION_LENGTH
        if len(caption) > max_len:
            return caption[:max_len - 3] + "..."
        return caption

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": os.path.getsize(file_path),
            "type": self.detect_type(file_path),
            "mime": self.get_mime_type(file_path),
        }
