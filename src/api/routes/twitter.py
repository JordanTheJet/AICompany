"""Twitter API routes"""

from fastapi import APIRouter, HTTPException, status
from src.models.schemas import TwitterPostRequest, PostResponse, Platform
from src.integrations import TwitterIntegration
from datetime import datetime

router = APIRouter(prefix="/twitter", tags=["Twitter"])


@router.post("/post", response_model=PostResponse)
async def post_to_twitter(request: TwitterPostRequest):
    """Post a tweet to Twitter

    Args:
        request: Twitter post request with text and optional media

    Returns:
        PostResponse with post details
    """
    try:
        integration = TwitterIntegration()

        # Post with or without media
        if request.media_paths:
            result = await integration.post_media(
                media_paths=request.media_paths,
                caption=request.text,
                reply_to_tweet_id=request.reply_to_tweet_id,
                quote_tweet_id=request.quote_tweet_id
            )
        else:
            result = await integration.post_text(
                text=request.text,
                reply_to_tweet_id=request.reply_to_tweet_id,
                quote_tweet_id=request.quote_tweet_id
            )

        if result["success"]:
            return PostResponse(
                success=True,
                platform=Platform.TWITTER,
                post_id=result.get("post_id"),
                post_url=result.get("post_url"),
                message=result.get("message", "Posted successfully")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to post tweet")
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/thread", response_model=PostResponse)
async def post_twitter_thread(tweets: list[str]):
    """Post a thread of tweets

    Args:
        tweets: List of tweet texts

    Returns:
        PostResponse with thread details
    """
    try:
        integration = TwitterIntegration()
        result = await integration.post_thread(tweets)

        if result["success"]:
            return PostResponse(
                success=True,
                platform=Platform.TWITTER,
                post_id=result.get("post_ids", [None])[0],
                post_url=result.get("post_url"),
                message=result.get("message", "Thread posted successfully")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to post thread")
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{post_id}")
async def delete_twitter_post(post_id: str):
    """Delete a tweet

    Args:
        post_id: Tweet ID to delete

    Returns:
        Success message
    """
    try:
        integration = TwitterIntegration()
        success = await integration.delete_post(post_id)

        if success:
            return {"success": True, "message": "Tweet deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete tweet"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{post_id}")
async def get_twitter_post(post_id: str):
    """Get tweet details

    Args:
        post_id: Tweet ID

    Returns:
        Tweet details
    """
    try:
        integration = TwitterIntegration()
        post = await integration.get_post(post_id)

        if post:
            return post
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tweet not found"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health/status")
async def twitter_health():
    """Check Twitter integration health

    Returns:
        Health status
    """
    try:
        integration = TwitterIntegration()
        health = await integration.health_check()
        return health
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
