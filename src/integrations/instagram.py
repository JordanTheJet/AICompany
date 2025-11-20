"""Instagram integration using Instagrapi"""

from instagrapi import Client
from typing import Dict, Any, List, Optional
from .base import BaseIntegration, retry_on_failure
from src.config import settings
from src.utils.media import MediaHandler
from pathlib import Path


class InstagramIntegration(BaseIntegration):
    """Instagram platform integration"""

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """Initialize Instagram integration

        Args:
            credentials: Instagram credentials
        """
        super().__init__(credentials)
        self.client = None

    def get_required_credentials(self) -> List[str]:
        """Get required Instagram credentials

        Returns:
            List of required credential keys
        """
        return ["username", "password"]

    async def authenticate(self) -> bool:
        """Authenticate with Instagram

        Returns:
            True if authentication successful
        """
        try:
            username = self.credentials.get("username") or settings.instagram_username
            password = self.credentials.get("password") or settings.instagram_password

            if not all([username, password]):
                raise ValueError("Missing required Instagram credentials")

            self.client = Client()

            # Try to load session if available
            session_file = Path(f"./credentials/instagram_{username}.json")
            if session_file.exists():
                try:
                    self.client.load_settings(session_file)
                    self.client.login(username, password)
                except Exception:
                    # Session invalid, login fresh
                    self.client.login(username, password)
                    self.client.dump_settings(session_file)
            else:
                # Fresh login
                self.client.login(username, password)
                session_file.parent.mkdir(exist_ok=True, parents=True)
                self.client.dump_settings(session_file)

            self.authenticated = True
            return True

        except Exception as e:
            print(f"Instagram authentication failed: {e}")
            self.authenticated = False
            return False

    @retry_on_failure(max_retries=3, delay=2.0)
    async def post_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """Instagram doesn't support text-only posts

        This will return an error directing users to use post_media instead
        """
        return {
            "success": False,
            "error": "Instagram does not support text-only posts",
            "message": "Please use post_media() to post an image with caption"
        }

    @retry_on_failure(max_retries=3, delay=2.0)
    async def post_media(
        self,
        media_paths: List[str],
        caption: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Post to Instagram feed

        Args:
            media_paths: List of image paths (1 for single post, 2-10 for carousel)
            caption: Post caption
            **kwargs: Additional parameters
                - location: Location name
                - user_tags: List of usernames to tag

        Returns:
            Dictionary with post result
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            location = kwargs.get("location")
            user_tags = kwargs.get("user_tags", [])

            # Validate all media files
            for media_path in media_paths:
                is_valid, error = MediaHandler.validate_instagram_media(media_path, "image")
                if not is_valid:
                    return {
                        "success": False,
                        "error": error,
                        "message": "Media validation failed"
                    }

            # Post based on number of images
            if len(media_paths) == 1:
                # Single image post
                media = self.client.photo_upload(
                    media_paths[0],
                    caption=caption or "",
                )
                post_id = media.pk
                post_url = f"https://www.instagram.com/p/{media.code}/"

            elif len(media_paths) > 1:
                # Carousel post (album)
                media = self.client.album_upload(
                    media_paths,
                    caption=caption or "",
                )
                post_id = media.pk
                post_url = f"https://www.instagram.com/p/{media.code}/"
            else:
                return {
                    "success": False,
                    "error": "No media files provided",
                    "message": "At least one image is required"
                }

            self._update_post_time()

            return {
                "success": True,
                "post_id": str(post_id),
                "post_url": post_url,
                "message": "Instagram post created successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to post to Instagram"
            }

    async def post_story(
        self,
        media_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Post an Instagram Story

        Args:
            media_path: Path to image or video
            **kwargs: Additional parameters

        Returns:
            Dictionary with post result
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            # Determine media type
            ext = MediaHandler.get_file_extension(media_path)
            is_video = ext in MediaHandler.INSTAGRAM_VIDEO_TYPES

            # Validate media
            media_type = "video" if is_video else "image"
            is_valid, error = MediaHandler.validate_instagram_media(media_path, media_type)
            if not is_valid:
                return {
                    "success": False,
                    "error": error,
                    "message": "Media validation failed"
                }

            # Upload story
            if is_video:
                story = self.client.video_upload_to_story(media_path)
            else:
                story = self.client.photo_upload_to_story(media_path)

            self._update_post_time()

            return {
                "success": True,
                "post_id": str(story.pk),
                "message": "Instagram story posted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to post Instagram story"
            }

    async def post_reel(
        self,
        video_path: str,
        caption: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Post an Instagram Reel

        Args:
            video_path: Path to video file
            caption: Reel caption
            **kwargs: Additional parameters

        Returns:
            Dictionary with post result
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            # Validate video
            is_valid, error = MediaHandler.validate_instagram_media(video_path, "video")
            if not is_valid:
                return {
                    "success": False,
                    "error": error,
                    "message": "Video validation failed"
                }

            # Upload reel
            reel = self.client.clip_upload(
                video_path,
                caption=caption or "",
            )

            self._update_post_time()

            post_url = f"https://www.instagram.com/p/{reel.code}/"

            return {
                "success": True,
                "post_id": str(reel.pk),
                "post_url": post_url,
                "message": "Instagram reel posted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to post Instagram reel"
            }

    async def delete_post(self, post_id: str) -> bool:
        """Delete an Instagram post

        Args:
            post_id: Media ID

        Returns:
            True if successful
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            self.client.media_delete(post_id)
            return True
        except Exception as e:
            print(f"Failed to delete Instagram post: {e}")
            return False

    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get Instagram post details

        Args:
            post_id: Media ID

        Returns:
            Dictionary with post details or None
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            media = self.client.media_info(post_id)
            return {
                "id": media.pk,
                "code": media.code,
                "caption": media.caption_text,
                "media_type": media.media_type,
                "like_count": media.like_count,
                "comment_count": media.comment_count,
                "created_at": media.taken_at
            }
        except Exception as e:
            print(f"Failed to get Instagram post: {e}")
            return None

    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user's information

        Returns:
            Dictionary with user info or None
        """
        if not self.authenticated:
            await self.authenticate()

        try:
            user_id = self.client.user_id
            user_info = self.client.user_info(user_id)
            return {
                "username": user_info.username,
                "full_name": user_info.full_name,
                "follower_count": user_info.follower_count,
                "following_count": user_info.following_count,
                "media_count": user_info.media_count,
                "biography": user_info.biography
            }
        except Exception as e:
            print(f"Failed to get user info: {e}")
            return None
