"""TikTok integration"""

import httpx
from typing import Dict, Any, List, Optional
from .base import BaseIntegration, retry_on_failure
from src.config import settings
from src.utils.media import MediaHandler
import json


class TikTokIntegration(BaseIntegration):
    """TikTok platform integration

    Note: This implementation uses TikTok's official API which requires
    developer approval. For testing, you'll need to register your app
    at https://developers.tiktok.com/
    """

    BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """Initialize TikTok integration

        Args:
            credentials: TikTok API credentials
        """
        super().__init__(credentials)
        self.access_token = None
        self.client = None

    def get_required_credentials(self) -> List[str]:
        """Get required TikTok credentials

        Returns:
            List of required credential keys
        """
        return ["client_key", "client_secret", "access_token"]

    async def authenticate(self) -> bool:
        """Authenticate with TikTok API

        Returns:
            True if authentication successful
        """
        try:
            client_key = self.credentials.get("client_key") or settings.tiktok_client_key
            client_secret = self.credentials.get("client_secret") or settings.tiktok_client_secret
            self.access_token = self.credentials.get("access_token") or settings.tiktok_access_token

            if not all([client_key, client_secret, self.access_token]):
                raise ValueError("Missing required TikTok credentials")

            # Create HTTP client
            self.client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
            )

            # Verify credentials by fetching user info
            response = await self.client.post(
                "/user/info/",
                json={"fields": ["display_name", "username"]}
            )

            if response.status_code == 200:
                self.authenticated = True
                return True
            else:
                raise ValueError(f"Authentication failed: {response.text}")

        except Exception as e:
            print(f"TikTok authentication failed: {e}")
            self.authenticated = False
            return False

    @retry_on_failure(max_retries=3, delay=2.0)
    async def post_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """TikTok doesn't support text-only posts

        This will return an error directing users to use post_media instead
        """
        return {
            "success": False,
            "error": "TikTok does not support text-only posts",
            "message": "Please use post_media() to upload a video with caption"
        }

    @retry_on_failure(max_retries=3, delay=2.0)
    async def post_media(
        self,
        media_paths: List[str],
        caption: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Post video to TikTok

        Args:
            media_paths: List with single video path (TikTok only allows one video)
            caption: Video caption/description
            **kwargs: Additional parameters
                - privacy_level: 'public', 'private', or 'followers'
                - allow_comments: Boolean
                - allow_duet: Boolean
                - allow_stitch: Boolean

        Returns:
            Dictionary with post result
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            if len(media_paths) != 1:
                return {
                    "success": False,
                    "error": "TikTok requires exactly one video file",
                    "message": "Please provide a single video path"
                }

            video_path = media_paths[0]

            # Validate video
            is_valid, error = MediaHandler.validate_tiktok_video(video_path)
            if not is_valid:
                return {
                    "success": False,
                    "error": error,
                    "message": "Video validation failed"
                }

            # Get video parameters
            privacy_level = kwargs.get("privacy_level", "public")
            allow_comments = kwargs.get("allow_comments", True)
            allow_duet = kwargs.get("allow_duet", True)
            allow_stitch = kwargs.get("allow_stitch", True)

            # Step 1: Initialize upload
            init_response = await self._initialize_upload()
            if not init_response:
                return {
                    "success": False,
                    "error": "Failed to initialize upload",
                    "message": "TikTok upload initialization failed"
                }

            upload_url = init_response.get("upload_url")
            publish_id = init_response.get("publish_id")

            # Step 2: Upload video
            upload_success = await self._upload_video(upload_url, video_path)
            if not upload_success:
                return {
                    "success": False,
                    "error": "Failed to upload video",
                    "message": "Video upload to TikTok failed"
                }

            # Step 3: Publish video
            publish_data = {
                "publish_id": publish_id,
                "title": caption or "",
                "privacy_level": privacy_level.upper(),
                "disable_comment": not allow_comments,
                "disable_duet": not allow_duet,
                "disable_stitch": not allow_stitch
            }

            publish_response = await self.client.post(
                "/post/publish/",
                json=publish_data
            )

            if publish_response.status_code == 200:
                result = publish_response.json()
                self._update_post_time()

                return {
                    "success": True,
                    "post_id": result.get("publish_id"),
                    "post_url": result.get("share_url"),
                    "message": "TikTok video posted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": publish_response.text,
                    "message": "Failed to publish TikTok video"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to post to TikTok"
            }

    async def _initialize_upload(self) -> Optional[Dict[str, Any]]:
        """Initialize TikTok video upload

        Returns:
            Dictionary with upload_url and publish_id or None
        """
        try:
            response = await self.client.post(
                "/post/publish/inbox/video/init/",
                json={"source_info": {"source": "FILE_UPLOAD"}}
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "upload_url": data.get("data", {}).get("upload_url"),
                    "publish_id": data.get("data", {}).get("publish_id")
                }
            return None
        except Exception as e:
            print(f"Failed to initialize TikTok upload: {e}")
            return None

    async def _upload_video(self, upload_url: str, video_path: str) -> bool:
        """Upload video file to TikTok

        Args:
            upload_url: Pre-signed upload URL from TikTok
            video_path: Path to video file

        Returns:
            True if successful
        """
        try:
            with open(video_path, "rb") as video_file:
                video_bytes = video_file.read()

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    upload_url,
                    content=video_bytes,
                    headers={"Content-Type": "video/mp4"}
                )

            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Failed to upload video to TikTok: {e}")
            return False

    async def delete_post(self, post_id: str) -> bool:
        """Delete a TikTok video

        Args:
            post_id: Video ID

        Returns:
            True if successful
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            response = await self.client.post(
                "/post/publish/cancel/",
                json={"publish_id": post_id}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to delete TikTok video: {e}")
            return False

    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get TikTok video details

        Args:
            post_id: Video ID

        Returns:
            Dictionary with video details or None
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            response = await self.client.post(
                "/video/query/",
                json={
                    "filters": {"video_ids": [post_id]},
                    "fields": [
                        "id",
                        "title",
                        "create_time",
                        "cover_image_url",
                        "share_url",
                        "video_description",
                        "duration",
                        "like_count",
                        "comment_count",
                        "share_count",
                        "view_count"
                    ]
                }
            )

            if response.status_code == 200:
                data = response.json()
                videos = data.get("data", {}).get("videos", [])
                if videos:
                    return videos[0]
            return None
        except Exception as e:
            print(f"Failed to get TikTok video: {e}")
            return None

    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user's information

        Returns:
            Dictionary with user info or None
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            response = await self.client.post(
                "/user/info/",
                json={
                    "fields": [
                        "display_name",
                        "username",
                        "avatar_url",
                        "follower_count",
                        "following_count",
                        "likes_count",
                        "video_count"
                    ]
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("user", {})
            return None
        except Exception as e:
            print(f"Failed to get TikTok user info: {e}")
            return None

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup HTTP client"""
        if self.client:
            await self.client.aclose()
