"""Twitter/X integration using Tweepy"""

import tweepy
from typing import Dict, Any, List, Optional
from .base import BaseIntegration, retry_on_failure
from src.config import settings
from src.utils.media import MediaHandler


class TwitterIntegration(BaseIntegration):
    """Twitter/X platform integration"""

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """Initialize Twitter integration

        Args:
            credentials: Twitter API credentials
        """
        super().__init__(credentials)
        self.api = None
        self.client_v2 = None

    def get_required_credentials(self) -> List[str]:
        """Get required Twitter credentials

        Returns:
            List of required credential keys
        """
        return [
            "api_key",
            "api_secret",
            "access_token",
            "access_token_secret"
        ]

    async def authenticate(self) -> bool:
        """Authenticate with Twitter API

        Returns:
            True if authentication successful
        """
        try:
            # Use credentials from constructor or fall back to settings
            api_key = self.credentials.get("api_key") or settings.twitter_api_key
            api_secret = self.credentials.get("api_secret") or settings.twitter_api_secret
            access_token = self.credentials.get("access_token") or settings.twitter_access_token
            access_token_secret = self.credentials.get("access_token_secret") or settings.twitter_access_token_secret
            bearer_token = self.credentials.get("bearer_token") or settings.twitter_bearer_token

            if not all([api_key, api_secret, access_token, access_token_secret]):
                raise ValueError("Missing required Twitter credentials")

            # OAuth 1.0a authentication (for API v1.1)
            auth = tweepy.OAuth1UserHandler(
                api_key,
                api_secret,
                access_token,
                access_token_secret
            )
            self.api = tweepy.API(auth)

            # Client for API v2
            self.client_v2 = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            # Verify credentials
            self.api.verify_credentials()
            self.authenticated = True
            return True

        except Exception as e:
            print(f"Twitter authentication failed: {e}")
            self.authenticated = False
            return False

    @retry_on_failure(max_retries=3, delay=2.0)
    async def post_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """Post a text tweet

        Args:
            text: Tweet text (max 280 characters)
            **kwargs: Additional parameters
                - reply_to_tweet_id: ID of tweet to reply to
                - quote_tweet_id: ID of tweet to quote

        Returns:
            Dictionary with post result
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            reply_to = kwargs.get("reply_to_tweet_id")
            quote_tweet = kwargs.get("quote_tweet_id")

            if quote_tweet:
                # Quote tweet
                response = self.client_v2.create_tweet(
                    text=text,
                    quote_tweet_id=quote_tweet
                )
            elif reply_to:
                # Reply to tweet
                response = self.client_v2.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=reply_to
                )
            else:
                # Regular tweet
                response = self.client_v2.create_tweet(text=text)

            self._update_post_time()

            tweet_id = response.data["id"]
            return {
                "success": True,
                "post_id": tweet_id,
                "post_url": f"https://twitter.com/user/status/{tweet_id}",
                "message": "Tweet posted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to post tweet"
            }

    @retry_on_failure(max_retries=3, delay=2.0)
    async def post_media(
        self,
        media_paths: List[str],
        caption: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Post tweet with media

        Args:
            media_paths: List of paths to media files (max 4 images or 1 video)
            caption: Tweet text
            **kwargs: Additional parameters

        Returns:
            Dictionary with post result
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            # Validate media files
            media_ids = []
            for media_path in media_paths:
                # Determine media type
                ext = MediaHandler.get_file_extension(media_path)
                media_type = "video" if ext in MediaHandler.TWITTER_VIDEO_TYPES else "image"

                # Validate media
                is_valid, error = MediaHandler.validate_twitter_media(media_path, media_type)
                if not is_valid:
                    return {
                        "success": False,
                        "error": error,
                        "message": "Media validation failed"
                    }

                # Upload media
                media = self.api.media_upload(media_path)
                media_ids.append(media.media_id)

            # Create tweet with media
            response = self.client_v2.create_tweet(
                text=caption or "",
                media_ids=media_ids
            )

            self._update_post_time()

            tweet_id = response.data["id"]
            return {
                "success": True,
                "post_id": tweet_id,
                "post_url": f"https://twitter.com/user/status/{tweet_id}",
                "message": "Tweet with media posted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to post tweet with media"
            }

    async def post_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """Post a thread of tweets

        Args:
            tweets: List of tweet texts

        Returns:
            Dictionary with post result
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            thread_ids = []
            reply_to_id = None

            for tweet_text in tweets:
                if reply_to_id:
                    response = self.client_v2.create_tweet(
                        text=tweet_text,
                        in_reply_to_tweet_id=reply_to_id
                    )
                else:
                    response = self.client_v2.create_tweet(text=tweet_text)

                tweet_id = response.data["id"]
                thread_ids.append(tweet_id)
                reply_to_id = tweet_id

            self._update_post_time()

            return {
                "success": True,
                "post_ids": thread_ids,
                "post_url": f"https://twitter.com/user/status/{thread_ids[0]}",
                "message": f"Thread of {len(tweets)} tweets posted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to post thread"
            }

    async def delete_post(self, post_id: str) -> bool:
        """Delete a tweet

        Args:
            post_id: Tweet ID

        Returns:
            True if successful
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            self.client_v2.delete_tweet(post_id)
            return True
        except Exception as e:
            print(f"Failed to delete tweet: {e}")
            return False

    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get tweet details

        Args:
            post_id: Tweet ID

        Returns:
            Dictionary with tweet details or None
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            response = self.client_v2.get_tweet(
                post_id,
                tweet_fields=["created_at", "public_metrics", "author_id"]
            )

            tweet = response.data
            return {
                "id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "metrics": tweet.public_metrics
            }
        except Exception as e:
            print(f"Failed to get tweet: {e}")
            return None

    async def check_rate_limit(self) -> bool:
        """Check Twitter rate limits

        Returns:
            True if posting is allowed
        """
        if not self.authenticated:
            return False

        try:
            # Get rate limit status
            rate_limit = self.api.rate_limit_status()
            tweet_limit = rate_limit["resources"]["statuses"]["/statuses/update"]
            self.rate_limit_remaining = tweet_limit["remaining"]
            return self.rate_limit_remaining > 0
        except Exception as e:
            print(f"Failed to check rate limit: {e}")
            return True  # Allow posting if rate limit check fails
