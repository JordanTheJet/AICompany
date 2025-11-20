"""Post management and multi-platform posting API routes"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.database import get_db
from src.services import PostService, ProfileService, EngagementService
from src.integrations import TwitterIntegration, InstagramIntegration, TikTokIntegration
from src.models.database import Platform, PostStatus

router = APIRouter(prefix="/posts", tags=["Posts"])


# Request/Response Models
class MultiPlatformPostRequest(BaseModel):
    """Multi-platform post request"""
    profile_id: int
    content: str
    media_paths: Optional[List[str]] = []
    platforms: List[str]  # List of platforms to post to
    scheduled_at: Optional[datetime] = None
    auto_engagement_enabled: bool = True


class PostResponse(BaseModel):
    """Post response"""
    id: int
    profile_id: int
    platform: str
    content: str
    status: str
    platform_post_id: Optional[str]
    platform_post_url: Optional[str]
    published_at: Optional[datetime]
    like_count: int
    comment_count: int

    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    """Single platform post creation"""
    profile_id: int
    social_account_id: int
    platform: str
    content: str
    media_urls: Optional[List[str]] = []
    scheduled_at: Optional[datetime] = None
    auto_engagement_enabled: bool = True


# Endpoints
@router.post("/create", response_model=List[PostResponse], status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: Session = Depends(get_db)):
    """Create a post"""
    post_service = PostService(db)

    # Convert platform string to enum
    try:
        platform = Platform[post.platform.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {post.platform}"
        )

    created_post = post_service.create_post(
        profile_id=post.profile_id,
        social_account_id=post.social_account_id,
        platform=platform,
        content=post.content,
        media_urls=post.media_urls,
        scheduled_at=post.scheduled_at,
        auto_engagement_enabled=post.auto_engagement_enabled
    )
    return [created_post]


@router.post("/multi-platform", response_model=List[PostResponse], status_code=status.HTTP_201_CREATED)
async def post_to_multiple_platforms(
    request: MultiPlatformPostRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Post content to multiple social media platforms simultaneously

    This endpoint allows posting the same content across Twitter, Instagram, and TikTok
    with automatic engagement from other profiles.
    """
    profile_service = ProfileService(db)
    post_service = PostService(db)
    engagement_service = EngagementService(db)

    # Verify profile exists
    profile = profile_service.get_profile(request.profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    created_posts = []
    errors = []

    # Post to each platform
    for platform_name in request.platforms:
        try:
            # Convert platform string to enum
            try:
                platform = Platform[platform_name.upper()]
            except KeyError:
                errors.append(f"Invalid platform: {platform_name}")
                continue

            # Get social account for this platform
            accounts = profile_service.get_profile_social_accounts(
                profile_id=request.profile_id,
                platform=platform,
                active_only=True
            )

            if not accounts:
                errors.append(f"No active {platform_name} account found for profile")
                continue

            social_account = accounts[0]

            # Create post in database
            post = post_service.create_post(
                profile_id=request.profile_id,
                social_account_id=social_account.id,
                platform=platform,
                content=request.content,
                media_urls=request.media_paths,
                scheduled_at=request.scheduled_at,
                auto_engagement_enabled=request.auto_engagement_enabled
            )

            # If not scheduled, publish immediately
            if not request.scheduled_at:
                # Publish post to platform
                result = await publish_post_to_platform(
                    post=post,
                    social_account=social_account,
                    content=request.content,
                    media_paths=request.media_paths,
                    post_service=post_service
                )

                if result["success"]:
                    # Schedule engagement actions in background
                    if request.auto_engagement_enabled:
                        background_tasks.add_task(
                            schedule_engagement_for_post,
                            post.id,
                            db
                        )

            created_posts.append(post)

        except Exception as e:
            errors.append(f"Error posting to {platform_name}: {str(e)}")

    if errors:
        # Return partial success with errors
        return created_posts  # Could also include errors in response

    return created_posts


async def publish_post_to_platform(
    post,
    social_account,
    content: str,
    media_paths: List[str],
    post_service: PostService
):
    """Publish post to social media platform"""
    try:
        platform = social_account.platform
        credentials = social_account.credentials

        # Get appropriate integration
        if platform == Platform.TWITTER:
            integration = TwitterIntegration(credentials=credentials)
            if media_paths:
                result = await integration.post_media(media_paths, content)
            else:
                result = await integration.post_text(content)

        elif platform == Platform.INSTAGRAM:
            integration = InstagramIntegration(credentials=credentials)
            if media_paths:
                result = await integration.post_media(media_paths, content)
            else:
                return {"success": False, "error": "Instagram requires media"}

        elif platform == Platform.TIKTOK:
            integration = TikTokIntegration(credentials=credentials)
            if media_paths:
                result = await integration.post_media(media_paths, content)
            else:
                return {"success": False, "error": "TikTok requires video"}

        else:
            return {"success": False, "error": "Unsupported platform"}

        # Update post with platform details
        if result["success"]:
            post_service.mark_as_published(
                post.id,
                platform_post_id=result.get("post_id"),
                platform_post_url=result.get("post_url")
            )
        else:
            post_service.mark_as_failed(post.id, result.get("error", "Unknown error"))

        return result

    except Exception as e:
        post_service.mark_as_failed(post.id, str(e))
        return {"success": False, "error": str(e)}


def schedule_engagement_for_post(post_id: int, db: Session):
    """Background task to schedule engagement actions for a post"""
    try:
        engagement_service = EngagementService(db)
        post_service = PostService(db)

        post = post_service.get_post(post_id)
        if post:
            engagement_service.schedule_engagement_actions(post)
    except Exception as e:
        print(f"Error scheduling engagement: {e}")


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get post by ID"""
    service = PostService(db)
    post = service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post


@router.get("/profile/{profile_id}", response_model=List[PostResponse])
async def get_profile_posts(
    profile_id: int,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get posts for a profile"""
    service = PostService(db)

    platform_enum = None
    if platform:
        try:
            platform_enum = Platform[platform.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}"
            )

    status_enum = None
    if status:
        try:
            status_enum = PostStatus[status.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )

    posts = service.get_profile_posts(
        profile_id=profile_id,
        platform=platform_enum,
        status=status_enum,
        limit=limit
    )
    return posts


@router.delete("/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete post"""
    service = PostService(db)
    success = service.delete_post(post_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return {"success": True, "message": "Post deleted"}


@router.put("/{post_id}/metrics")
async def update_post_metrics(
    post_id: int,
    metrics: Dict[str, int],
    db: Session = Depends(get_db)
):
    """Update engagement metrics for a post"""
    service = PostService(db)
    post = service.update_engagement_metrics(
        post_id=post_id,
        like_count=metrics.get("like_count"),
        comment_count=metrics.get("comment_count"),
        share_count=metrics.get("share_count"),
        view_count=metrics.get("view_count")
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post
