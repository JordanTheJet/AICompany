"""Media handling utilities"""

import os
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
import hashlib


class MediaHandler:
    """Handles media file validation and processing"""

    # Supported file types by platform
    TWITTER_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    TWITTER_VIDEO_TYPES = {".mp4", ".mov"}
    INSTAGRAM_IMAGE_TYPES = {".jpg", ".jpeg", ".png"}
    INSTAGRAM_VIDEO_TYPES = {".mp4", ".mov"}
    TIKTOK_VIDEO_TYPES = {".mp4", ".mov", ".avi", ".webm"}

    # File size limits (in bytes)
    TWITTER_IMAGE_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
    TWITTER_VIDEO_MAX_SIZE = 512 * 1024 * 1024  # 512 MB
    INSTAGRAM_IMAGE_MAX_SIZE = 8 * 1024 * 1024  # 8 MB
    INSTAGRAM_VIDEO_MAX_SIZE = 100 * 1024 * 1024  # 100 MB
    TIKTOK_VIDEO_MAX_SIZE = 287 * 1024 * 1024  # 287 MB

    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate that a file exists and is readable

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(file_path)

        if not path.exists():
            return False, f"File not found: {file_path}"

        if not path.is_file():
            return False, f"Path is not a file: {file_path}"

        if not os.access(path, os.R_OK):
            return False, f"File is not readable: {file_path}"

        return True, None

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension in lowercase

        Args:
            file_path: Path to the file

        Returns:
            File extension including dot (e.g., '.jpg')
        """
        return Path(file_path).suffix.lower()

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes
        """
        return os.path.getsize(file_path)

    @staticmethod
    def get_mime_type(file_path: str) -> Optional[str]:
        """Get MIME type of a file

        Args:
            file_path: Path to the file

        Returns:
            MIME type string or None
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type

    @classmethod
    def validate_twitter_media(cls, file_path: str, media_type: str = "image") -> Tuple[bool, Optional[str]]:
        """Validate media file for Twitter

        Args:
            file_path: Path to media file
            media_type: Type of media ('image' or 'video')

        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, error = cls.validate_file(file_path)
        if not is_valid:
            return False, error

        ext = cls.get_file_extension(file_path)
        size = cls.get_file_size(file_path)

        if media_type == "image":
            if ext not in cls.TWITTER_IMAGE_TYPES:
                return False, f"Unsupported image format for Twitter: {ext}"
            if size > cls.TWITTER_IMAGE_MAX_SIZE:
                return False, f"Image too large for Twitter: {size / 1024 / 1024:.2f} MB (max 5 MB)"
        elif media_type == "video":
            if ext not in cls.TWITTER_VIDEO_TYPES:
                return False, f"Unsupported video format for Twitter: {ext}"
            if size > cls.TWITTER_VIDEO_MAX_SIZE:
                return False, f"Video too large for Twitter: {size / 1024 / 1024:.2f} MB (max 512 MB)"

        return True, None

    @classmethod
    def validate_instagram_media(cls, file_path: str, media_type: str = "image") -> Tuple[bool, Optional[str]]:
        """Validate media file for Instagram

        Args:
            file_path: Path to media file
            media_type: Type of media ('image' or 'video')

        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, error = cls.validate_file(file_path)
        if not is_valid:
            return False, error

        ext = cls.get_file_extension(file_path)
        size = cls.get_file_size(file_path)

        if media_type == "image":
            if ext not in cls.INSTAGRAM_IMAGE_TYPES:
                return False, f"Unsupported image format for Instagram: {ext}"
            if size > cls.INSTAGRAM_IMAGE_MAX_SIZE:
                return False, f"Image too large for Instagram: {size / 1024 / 1024:.2f} MB (max 8 MB)"
        elif media_type == "video":
            if ext not in cls.INSTAGRAM_VIDEO_TYPES:
                return False, f"Unsupported video format for Instagram: {ext}"
            if size > cls.INSTAGRAM_VIDEO_MAX_SIZE:
                return False, f"Video too large for Instagram: {size / 1024 / 1024:.2f} MB (max 100 MB)"

        return True, None

    @classmethod
    def validate_tiktok_video(cls, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate video file for TikTok

        Args:
            file_path: Path to video file

        Returns:
            Tuple of (is_valid, error_message)
        """
        is_valid, error = cls.validate_file(file_path)
        if not is_valid:
            return False, error

        ext = cls.get_file_extension(file_path)
        size = cls.get_file_size(file_path)

        if ext not in cls.TIKTOK_VIDEO_TYPES:
            return False, f"Unsupported video format for TikTok: {ext}"

        if size > cls.TIKTOK_VIDEO_MAX_SIZE:
            return False, f"Video too large for TikTok: {size / 1024 / 1024:.2f} MB (max 287 MB)"

        return True, None

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate MD5 hash of a file

        Args:
            file_path: Path to the file

        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
