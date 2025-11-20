"""Tests for media utilities"""

import pytest
from src.utils.media import MediaHandler
import tempfile
import os


def test_get_file_extension():
    """Test file extension extraction"""
    assert MediaHandler.get_file_extension("image.jpg") == ".jpg"
    assert MediaHandler.get_file_extension("video.MP4") == ".mp4"
    assert MediaHandler.get_file_extension("/path/to/file.PNG") == ".png"


def test_validate_file_not_exists():
    """Test validation for non-existent file"""
    is_valid, error = MediaHandler.validate_file("/nonexistent/file.jpg")
    assert is_valid is False
    assert "not found" in error


def test_validate_file_exists():
    """Test validation for existing file"""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name

    try:
        is_valid, error = MediaHandler.validate_file(tmp_path)
        assert is_valid is True
        assert error is None
    finally:
        os.unlink(tmp_path)


def test_twitter_image_types():
    """Test Twitter supported image types"""
    assert ".jpg" in MediaHandler.TWITTER_IMAGE_TYPES
    assert ".png" in MediaHandler.TWITTER_IMAGE_TYPES
    assert ".gif" in MediaHandler.TWITTER_IMAGE_TYPES


def test_instagram_image_types():
    """Test Instagram supported image types"""
    assert ".jpg" in MediaHandler.INSTAGRAM_IMAGE_TYPES
    assert ".png" in MediaHandler.INSTAGRAM_IMAGE_TYPES


def test_tiktok_video_types():
    """Test TikTok supported video types"""
    assert ".mp4" in MediaHandler.TIKTOK_VIDEO_TYPES
    assert ".mov" in MediaHandler.TIKTOK_VIDEO_TYPES


def test_get_mime_type():
    """Test MIME type detection"""
    assert MediaHandler.get_mime_type("image.jpg") == "image/jpeg"
    assert MediaHandler.get_mime_type("video.mp4") == "video/mp4"
    assert MediaHandler.get_mime_type("image.png") == "image/png"
