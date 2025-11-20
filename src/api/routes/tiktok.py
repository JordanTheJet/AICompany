"""TikTok API routes"""

from fastapi import APIRouter, HTTPException, status
from src.models.schemas import TikTokPostRequest, PostResponse, Platform
from src.integrations import TikTokIntegration

router = APIRouter(prefix="/tiktok", tags=["TikTok"])


@router.post("/post", response_model=PostResponse)
async def post_to_tiktok(request: TikTokPostRequest):
    """Post a video to TikTok

    Args:
        request: TikTok post request with video and caption

    Returns:
        PostResponse with post details
    """
    try:
        integration = TikTokIntegration()

        result = await integration.post_media(
            media_paths=[request.video_path],
            caption=request.caption,
            privacy_level=request.privacy_level.value,
            allow_comments=request.allow_comments,
            allow_duet=request.allow_duet,
            allow_stitch=request.allow_stitch
        )

        if result["success"]:
            return PostResponse(
                success=True,
                platform=Platform.TIKTOK,
                post_id=result.get("post_id"),
                post_url=result.get("post_url"),
                message=result.get("message", "Posted successfully")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to post to TikTok")
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{post_id}")
async def delete_tiktok_post(post_id: str):
    """Delete a TikTok video

    Args:
        post_id: Video ID to delete

    Returns:
        Success message
    """
    try:
        integration = TikTokIntegration()
        success = await integration.delete_post(post_id)

        if success:
            return {"success": True, "message": "Video deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete video"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{post_id}")
async def get_tiktok_post(post_id: str):
    """Get TikTok video details

    Args:
        post_id: Video ID

    Returns:
        Video details
    """
    try:
        integration = TikTokIntegration()
        post = await integration.get_post(post_id)

        if post:
            return post
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/info")
async def get_tiktok_user_info():
    """Get authenticated user's TikTok info

    Returns:
        User information
    """
    try:
        integration = TikTokIntegration()
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
async def tiktok_health():
    """Check TikTok integration health

    Returns:
        Health status
    """
    try:
        integration = TikTokIntegration()
        health = await integration.health_check()
        return health
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
