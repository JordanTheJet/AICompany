"""Database models for profile and engagement system"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Float, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class Platform(enum.Enum):
    """Social media platforms"""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class EngagementType(enum.Enum):
    """Types of engagement actions"""
    LIKE = "like"
    COMMENT = "comment"
    RETWEET = "retweet"
    SHARE = "share"


class PostStatus(enum.Enum):
    """Status of a post"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class User(Base):
    """User of the platform"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profiles = relationship("Profile", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    """A persona/character with its own social media presence"""
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    description = Column(Text)
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)

    # Engagement settings
    auto_engage = Column(Boolean, default=False)
    engagement_delay_min = Column(Integer, default=5)  # Min minutes before engaging
    engagement_delay_max = Column(Integer, default=60)  # Max minutes before engaging

    # Metadata
    metadata = Column(JSON)  # Store additional profile info (personality traits, topics, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profiles")
    social_accounts = relationship("SocialAccount", back_populates="profile", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="profile", cascade="all, delete-orphan")
    engagement_rules = relationship("EngagementRule", foreign_keys="EngagementRule.profile_id", back_populates="profile")
    target_rules = relationship("EngagementRule", foreign_keys="EngagementRule.target_profile_id", back_populates="target_profile")
    engagement_actions = relationship("EngagementAction", back_populates="profile")


class SocialAccount(Base):
    """Links a profile to a specific social media account"""
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    platform = Column(SQLEnum(Platform), nullable=False)

    # Account details
    platform_user_id = Column(String(255))  # User ID on the platform
    platform_username = Column(String(255))
    platform_display_name = Column(String(255))

    # Credentials (encrypted in practice)
    credentials = Column(JSON, nullable=False)  # Platform-specific credentials

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_auth_at = Column(DateTime)

    # Metadata
    metadata = Column(JSON)  # Store platform-specific metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("Profile", back_populates="social_accounts")
    posts = relationship("Post", back_populates="social_account")


class Post(Base):
    """A post made by a profile on a social platform"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=False)

    # Post content
    content = Column(Text, nullable=False)
    media_urls = Column(JSON)  # List of media URLs

    # Platform details
    platform = Column(SQLEnum(Platform), nullable=False)
    platform_post_id = Column(String(255))  # ID on the platform
    platform_post_url = Column(String(500))  # URL to the post

    # Status
    status = Column(SQLEnum(PostStatus), default=PostStatus.DRAFT)

    # Scheduling
    scheduled_at = Column(DateTime)
    published_at = Column(DateTime)

    # Engagement tracking
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # Auto-engagement
    auto_engagement_enabled = Column(Boolean, default=True)
    engagement_completed = Column(Boolean, default=False)

    # Metadata
    metadata = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("Profile", back_populates="posts")
    social_account = relationship("SocialAccount", back_populates="posts")
    engagement_actions = relationship("EngagementAction", back_populates="post")


class EngagementRule(Base):
    """Rules for automated engagement between profiles"""
    __tablename__ = "engagement_rules"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)  # Profile that will engage
    target_profile_id = Column(Integer, ForeignKey("profiles.id"))  # Target profile (null = all profiles)

    # Rule configuration
    is_active = Column(Boolean, default=True)
    engagement_types = Column(JSON, nullable=False)  # List of engagement types: ["like", "comment", "retweet"]

    # Probability settings (0.0 to 1.0)
    like_probability = Column(Float, default=0.8)
    comment_probability = Column(Float, default=0.3)
    retweet_probability = Column(Float, default=0.1)
    share_probability = Column(Float, default=0.1)

    # Timing settings (in minutes)
    min_delay = Column(Integer, default=5)
    max_delay = Column(Integer, default=60)

    # Comment settings
    comment_templates = Column(JSON)  # List of comment templates
    use_ai_comments = Column(Boolean, default=False)

    # Platform filters
    platforms = Column(JSON)  # List of platforms to engage on (null = all)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("Profile", foreign_keys=[profile_id], back_populates="engagement_rules")
    target_profile = relationship("Profile", foreign_keys=[target_profile_id], back_populates="target_rules")


class EngagementAction(Base):
    """Tracks engagement actions performed by profiles"""
    __tablename__ = "engagement_actions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    # Action details
    engagement_type = Column(SQLEnum(EngagementType), nullable=False)
    platform = Column(SQLEnum(Platform), nullable=False)

    # Status
    status = Column(String(50), default="pending")  # pending, completed, failed
    scheduled_at = Column(DateTime)
    executed_at = Column(DateTime)

    # Content (for comments)
    content = Column(Text)

    # Platform response
    platform_action_id = Column(String(255))  # ID of like/comment on platform
    error_message = Column(Text)

    # Metadata
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("Profile", back_populates="engagement_actions")
    post = relationship("Post", back_populates="engagement_actions")
