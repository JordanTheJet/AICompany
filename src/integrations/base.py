"""Base integration class for all social media platforms"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
from functools import wraps


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry failed operations

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator


class BaseIntegration(ABC):
    """Abstract base class for social media integrations"""

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """Initialize integration

        Args:
            credentials: Platform-specific credentials
        """
        self.credentials = credentials or {}
        self.client = None
        self.authenticated = False
        self.rate_limit_remaining = None
        self.last_post_time: Optional[datetime] = None

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform

        Returns:
            True if authentication successful, False otherwise
        """
        pass

    @abstractmethod
    async def post_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """Post text content

        Args:
            text: Text content to post
            **kwargs: Platform-specific parameters

        Returns:
            Dictionary containing post result
        """
        pass

    @abstractmethod
    async def post_media(
        self,
        media_paths: List[str],
        caption: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Post media content

        Args:
            media_paths: List of paths to media files
            caption: Optional caption for the media
            **kwargs: Platform-specific parameters

        Returns:
            Dictionary containing post result
        """
        pass

    @abstractmethod
    async def delete_post(self, post_id: str) -> bool:
        """Delete a post

        Args:
            post_id: ID of the post to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get post details

        Args:
            post_id: ID of the post

        Returns:
            Dictionary containing post details or None
        """
        pass

    async def check_rate_limit(self) -> bool:
        """Check if rate limit allows posting

        Returns:
            True if posting is allowed, False otherwise
        """
        # Override in subclass for platform-specific rate limiting
        return True

    async def validate_credentials(self) -> bool:
        """Validate that credentials are present and valid

        Returns:
            True if credentials are valid, False otherwise
        """
        if not self.credentials:
            return False

        required_keys = self.get_required_credentials()
        return all(key in self.credentials for key in required_keys)

    @abstractmethod
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential keys

        Returns:
            List of required credential key names
        """
        pass

    def get_platform_name(self) -> str:
        """Get the platform name

        Returns:
            Platform name string
        """
        return self.__class__.__name__.replace("Integration", "").lower()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the integration

        Returns:
            Dictionary containing health check results
        """
        return {
            "platform": self.get_platform_name(),
            "authenticated": self.authenticated,
            "rate_limit_remaining": self.rate_limit_remaining,
            "last_post_time": self.last_post_time.isoformat() if self.last_post_time else None,
            "status": "healthy" if self.authenticated else "not_authenticated"
        }

    def _update_post_time(self):
        """Update the last post timestamp"""
        self.last_post_time = datetime.utcnow()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Cleanup if needed
        pass
