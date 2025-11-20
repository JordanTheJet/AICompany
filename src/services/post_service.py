"""Post management service"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from src.models.database import Post, Profile, SocialAccount, Platform, PostStatus
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PostService:
    """Service for managing posts"""

    def __init__(self, db: Session):
        """Initialize post service

        Args:
            db: Database session
        """
        self.db = db

    def create_post(
        self,
        profile_id: int,
        social_account_id: int,
        platform: Platform,
        content: str,
        media_urls: Optional[List[str]] = None,
        scheduled_at: Optional[datetime] = None,
        auto_engagement_enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Post:
        """Create a new post

        Args:
            profile_id: Profile ID
            social_account_id: Social account ID
            platform: Platform
            content: Post content
            media_urls: List of media URLs
            scheduled_at: Schedule time
            auto_engagement_enabled: Enable auto-engagement
            metadata: Additional metadata

        Returns:
            Created post
        """
        status = PostStatus.SCHEDULED if scheduled_at else PostStatus.DRAFT

        post = Post(
            profile_id=profile_id,
            social_account_id=social_account_id,
            platform=platform,
            content=content,
            media_urls=media_urls or [],
            status=status,
            scheduled_at=scheduled_at,
            auto_engagement_enabled=auto_engagement_enabled,
            metadata=metadata or {}
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        logger.info(f"Created post {post.id} for profile {profile_id}")
        return post

    def get_post(self, post_id: int) -> Optional[Post]:
        """Get post by ID

        Args:
            post_id: Post ID

        Returns:
            Post or None
        """
        return self.db.query(Post).filter(Post.id == post_id).first()

    def get_profile_posts(
        self,
        profile_id: int,
        platform: Optional[Platform] = None,
        status: Optional[PostStatus] = None,
        limit: int = 100
    ) -> List[Post]:
        """Get posts for a profile

        Args:
            profile_id: Profile ID
            platform: Filter by platform
            status: Filter by status
            limit: Maximum number of posts

        Returns:
            List of posts
        """
        query = self.db.query(Post).filter(Post.profile_id == profile_id)
        if platform:
            query = query.filter(Post.platform == platform)
        if status:
            query = query.filter(Post.status == status)
        return query.order_by(Post.created_at.desc()).limit(limit).all()

    def get_recent_posts(
        self,
        platform: Optional[Platform] = None,
        status: Optional[PostStatus] = None,
        exclude_profile_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Post]:
        """Get recent posts across all profiles

        Args:
            platform: Filter by platform
            status: Filter by status
            exclude_profile_id: Exclude posts from this profile
            limit: Maximum number of posts

        Returns:
            List of posts
        """
        query = self.db.query(Post)
        if platform:
            query = query.filter(Post.platform == platform)
        if status:
            query = query.filter(Post.status == status)
        if exclude_profile_id:
            query = query.filter(Post.profile_id != exclude_profile_id)

        return query.order_by(Post.published_at.desc()).limit(limit).all()

    def update_post(
        self,
        post_id: int,
        **kwargs
    ) -> Optional[Post]:
        """Update post

        Args:
            post_id: Post ID
            **kwargs: Fields to update

        Returns:
            Updated post or None
        """
        post = self.get_post(post_id)
        if not post:
            return None

        for key, value in kwargs.items():
            if hasattr(post, key):
                setattr(post, key, value)

        post.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(post)
        logger.info(f"Updated post: {post_id}")
        return post

    def mark_as_published(
        self,
        post_id: int,
        platform_post_id: str,
        platform_post_url: Optional[str] = None
    ) -> Optional[Post]:
        """Mark post as published

        Args:
            post_id: Post ID
            platform_post_id: ID on the platform
            platform_post_url: URL on the platform

        Returns:
            Updated post or None
        """
        return self.update_post(
            post_id,
            status=PostStatus.PUBLISHED,
            platform_post_id=platform_post_id,
            platform_post_url=platform_post_url,
            published_at=datetime.utcnow()
        )

    def mark_as_failed(
        self,
        post_id: int,
        error_message: str
    ) -> Optional[Post]:
        """Mark post as failed

        Args:
            post_id: Post ID
            error_message: Error message

        Returns:
            Updated post or None
        """
        return self.update_post(
            post_id,
            status=PostStatus.FAILED,
            error_message=error_message
        )

    def update_engagement_metrics(
        self,
        post_id: int,
        like_count: Optional[int] = None,
        comment_count: Optional[int] = None,
        share_count: Optional[int] = None,
        view_count: Optional[int] = None
    ) -> Optional[Post]:
        """Update engagement metrics for a post

        Args:
            post_id: Post ID
            like_count: Number of likes
            comment_count: Number of comments
            share_count: Number of shares
            view_count: Number of views

        Returns:
            Updated post or None
        """
        updates = {}
        if like_count is not None:
            updates['like_count'] = like_count
        if comment_count is not None:
            updates['comment_count'] = comment_count
        if share_count is not None:
            updates['share_count'] = share_count
        if view_count is not None:
            updates['view_count'] = view_count

        return self.update_post(post_id, **updates)

    def get_posts_for_engagement(
        self,
        profile_id: int,
        platform: Optional[Platform] = None,
        limit: int = 50
    ) -> List[Post]:
        """Get posts that need engagement from other profiles

        Args:
            profile_id: Profile ID to exclude (own posts)
            platform: Filter by platform
            limit: Maximum number of posts

        Returns:
            List of posts ready for engagement
        """
        query = self.db.query(Post).filter(
            Post.profile_id != profile_id,
            Post.status == PostStatus.PUBLISHED,
            Post.auto_engagement_enabled == True,
            Post.engagement_completed == False
        )

        if platform:
            query = query.filter(Post.platform == platform)

        return query.order_by(Post.published_at.desc()).limit(limit).all()

    def mark_engagement_completed(self, post_id: int) -> Optional[Post]:
        """Mark post engagement as completed

        Args:
            post_id: Post ID

        Returns:
            Updated post or None
        """
        return self.update_post(post_id, engagement_completed=True)

    def delete_post(self, post_id: int) -> bool:
        """Delete post

        Args:
            post_id: Post ID

        Returns:
            True if successful
        """
        post = self.get_post(post_id)
        if not post:
            return False

        self.db.delete(post)
        self.db.commit()
        logger.info(f"Deleted post: {post_id}")
        return True
