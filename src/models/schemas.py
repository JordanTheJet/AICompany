"""Pydantic schemas for API requests and responses"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    """Supported social media platforms"""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class MediaType(str, Enum):
    """Media types for posts"""
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"


class PrivacyLevel(str, Enum):
    """Privacy levels for posts"""
    PUBLIC = "public"
    PRIVATE = "private"
    FOLLOWERS = "followers"


class MediaUpload(BaseModel):
    """Media upload schema"""
    media_type: MediaType
    file_path: Optional[str] = None
    url: Optional[HttpUrl] = None
    alt_text: Optional[str] = None


class PostRequest(BaseModel):
    """Base post request schema"""
    platform: Platform
    content: str = Field(..., max_length=5000)
    media: Optional[List[MediaUpload]] = []
    scheduled_at: Optional[datetime] = None


class TwitterPostRequest(BaseModel):
    """Twitter-specific post request"""
    text: str = Field(..., max_length=280, description="Tweet text (max 280 characters)")
    media_paths: Optional[List[str]] = Field(default=[], description="Paths to media files")
    reply_to_tweet_id: Optional[str] = None
    quote_tweet_id: Optional[str] = None
    poll_options: Optional[List[str]] = None
    poll_duration_minutes: Optional[int] = None


class InstagramPostRequest(BaseModel):
    """Instagram-specific post request"""
    caption: str = Field(..., max_length=2200, description="Post caption")
    image_path: Optional[str] = Field(None, description="Path to image file")
    image_paths: Optional[List[str]] = Field(default=[], description="Paths for carousel posts")
    location: Optional[str] = None
    hashtags: Optional[List[str]] = []
    user_tags: Optional[List[str]] = []


class TikTokPostRequest(BaseModel):
    """TikTok-specific post request"""
    caption: str = Field(..., max_length=2200, description="Video caption")
    video_path: str = Field(..., description="Path to video file")
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    allow_comments: bool = True
    allow_duet: bool = True
    allow_stitch: bool = True
    hashtags: Optional[List[str]] = []


class PostResponse(BaseModel):
    """Post response schema"""
    success: bool
    platform: Platform
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IntegrationStatus(BaseModel):
    """Integration status response"""
    platform: Platform
    enabled: bool
    authenticated: bool
    rate_limit_remaining: Optional[int] = None
    last_post_at: Optional[datetime] = None
