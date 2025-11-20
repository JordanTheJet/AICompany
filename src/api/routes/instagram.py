"""Instagram API routes"""

from fastapi import APIRouter, HTTPException, status
from src.models.schemas import InstagramPostRequest, PostResponse, Platform
from src.integrations import InstagramIntegration
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/instagram", tags=["Instagram"])


class InstagramStoryRequest(BaseModel):
    """Instagram story request"""
    media_path: str


class InstagramReelRequest(BaseModel):
    """Instagram reel request"""
    video_path: str
    caption: Optional[str] = None


@router.post("/post", response_model=PostResponse)
async def post_to_instagram(request: InstagramPostRequest):
    """Post to Instagram feed

    Args:
        request: Instagram post request with image(s) and caption

    Returns:
        PostResponse with post details
    """
    try:
        integration = InstagramIntegration()

        # Determine media paths
        media_paths = []
        if request.image_path:
            media_paths.append(request.image_path)
        if request.image_paths:
            media_paths.extend(request.image_paths)

        if not media_paths:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one image is required"
            )

        result = await integration.post_media(
            media_paths=media_paths,
            caption=request.caption,
            location=request.location,
            user_tags=request.user_tags
        )

        if result["success"]:
            return PostResponse(
                success=True,
                platform=Platform.INSTAGRAM,
                post_id=result.get("post_id"),
                post_url=result.get("post_url"),
                message=result.get("message", "Posted successfully")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to post to Instagram")
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/story", response_model=PostResponse)
async def post_instagram_story(request: InstagramStoryRequest):
    """Post an Instagram story

    Args:
        request: Story request with media path

    Returns:
        PostResponse with story details
    """
    try:
        integration = InstagramIntegration()
        result = await integration.post_story(request.media_path)

        if result["success"]:
            return PostResponse(
                success=True,
                platform=Platform.INSTAGRAM,
                post_id=result.get("post_id"),
                message=result.get("message", "Story posted successfully")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to post story")
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reel", response_model=PostResponse)
async def post_instagram_reel(request: InstagramReelRequest):
    """Post an Instagram reel

    Args:
        request: Reel request with video and caption

    Returns:
        PostResponse with reel details
    """
    try:
        integration = InstagramIntegration()
        result = await integration.post_reel(
            video_path=request.video_path,
            caption=request.caption
        )

        if result["success"]:
            return PostResponse(
                success=True,
                platform=Platform.INSTAGRAM,
                post_id=result.get("post_id"),
                post_url=result.get("post_url"),
                message=result.get("message", "Reel posted successfully")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to post reel")
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{post_id}")
async def delete_instagram_post(post_id: str):
    """Delete an Instagram post

    Args:
        post_id: Post ID to delete

    Returns:
        Success message
    """
    try:
        integration = InstagramIntegration()
        success = await integration.delete_post(post_id)

        if success:
            return {"success": True, "message": "Post deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete post"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{post_id}")
async def get_instagram_post(post_id: str):
    """Get Instagram post details

    Args:
        post_id: Post ID

    Returns:
        Post details
    """
    try:
        integration = InstagramIntegration()
        post = await integration.get_post(post_id)

        if post:
            return post
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/info")
async def get_instagram_user_info():
    """Get authenticated user's Instagram info

    Returns:
        User information
    """
    try:
        integration = InstagramIntegration()
        user_info = await integration.get_user_info()

        if user_info:
            return user_info
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User info not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health/status")
async def instagram_health():
    """Check Instagram integration health

    Returns:
        Health status
    """
    try:
        integration = InstagramIntegration()
        health = await integration.health_check()
        return health
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
