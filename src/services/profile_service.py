"""Profile management service"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from src.models.database import User, Profile, SocialAccount, Platform
from src.utils.auth import AuthManager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles and social accounts"""

    def __init__(self, db: Session):
        """Initialize profile service

        Args:
            db: Database session
        """
        self.db = db
        self.auth_manager = AuthManager()

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None
    ) -> User:
        """Create a new user

        Args:
            email: User email
            username: Username
            password: Plain text password (will be hashed)
            full_name: Full name

        Returns:
            Created user
        """
        # In production, use proper password hashing (bcrypt, argon2, etc.)
        import hashlib
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Created user: {username}")
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID

        Args:
            user_id: User ID

        Returns:
            User or None
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username

        Args:
            username: Username

        Returns:
            User or None
        """
        return self.db.query(User).filter(User.username == username).first()

    def create_profile(
        self,
        user_id: int,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        avatar_url: Optional[str] = None,
        auto_engage: bool = False,
        engagement_delay_min: int = 5,
        engagement_delay_max: int = 60,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Profile:
        """Create a new profile (persona)

        Args:
            user_id: User ID
            name: Profile name
            display_name: Display name
            description: Profile description
            avatar_url: Avatar image URL
            auto_engage: Enable automatic engagement
            engagement_delay_min: Minimum engagement delay in minutes
            engagement_delay_max: Maximum engagement delay in minutes
            metadata: Additional metadata

        Returns:
            Created profile
        """
        profile = Profile(
            user_id=user_id,
            name=name,
            display_name=display_name or name,
            description=description,
            avatar_url=avatar_url,
            auto_engage=auto_engage,
            engagement_delay_min=engagement_delay_min,
            engagement_delay_max=engagement_delay_max,
            metadata=metadata or {}
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        logger.info(f"Created profile: {name} for user {user_id}")
        return profile

    def get_profile(self, profile_id: int) -> Optional[Profile]:
        """Get profile by ID

        Args:
            profile_id: Profile ID

        Returns:
            Profile or None
        """
        return self.db.query(Profile).filter(Profile.id == profile_id).first()

    def get_user_profiles(self, user_id: int, active_only: bool = True) -> List[Profile]:
        """Get all profiles for a user

        Args:
            user_id: User ID
            active_only: Only return active profiles

        Returns:
            List of profiles
        """
        query = self.db.query(Profile).filter(Profile.user_id == user_id)
        if active_only:
            query = query.filter(Profile.is_active == True)
        return query.all()

    def update_profile(
        self,
        profile_id: int,
        **kwargs
    ) -> Optional[Profile]:
        """Update profile

        Args:
            profile_id: Profile ID
            **kwargs: Fields to update

        Returns:
            Updated profile or None
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return None

        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        logger.info(f"Updated profile: {profile_id}")
        return profile

    def delete_profile(self, profile_id: int) -> bool:
        """Delete profile (soft delete by setting is_active to False)

        Args:
            profile_id: Profile ID

        Returns:
            True if successful
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return False

        profile.is_active = False
        self.db.commit()
        logger.info(f"Deleted profile: {profile_id}")
        return True

    def add_social_account(
        self,
        profile_id: int,
        platform: Platform,
        credentials: Dict[str, str],
        platform_username: Optional[str] = None,
        platform_user_id: Optional[str] = None,
        platform_display_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SocialAccount:
        """Add a social account to a profile

        Args:
            profile_id: Profile ID
            platform: Social media platform
            credentials: Platform credentials
            platform_username: Username on platform
            platform_user_id: User ID on platform
            platform_display_name: Display name on platform
            metadata: Additional metadata

        Returns:
            Created social account
        """
        # Encrypt credentials
        platform_name = platform.value if isinstance(platform, Platform) else platform
        self.auth_manager.save_credentials(f"{profile_id}_{platform_name}", credentials)

        account = SocialAccount(
            profile_id=profile_id,
            platform=platform,
            credentials=credentials,  # In production, store encrypted reference
            platform_username=platform_username,
            platform_user_id=platform_user_id,
            platform_display_name=platform_display_name,
            metadata=metadata or {}
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        logger.info(f"Added {platform_name} account to profile {profile_id}")
        return account

    def get_social_account(self, account_id: int) -> Optional[SocialAccount]:
        """Get social account by ID

        Args:
            account_id: Account ID

        Returns:
            Social account or None
        """
        return self.db.query(SocialAccount).filter(SocialAccount.id == account_id).first()

    def get_profile_social_accounts(
        self,
        profile_id: int,
        platform: Optional[Platform] = None,
        active_only: bool = True
    ) -> List[SocialAccount]:
        """Get social accounts for a profile

        Args:
            profile_id: Profile ID
            platform: Filter by platform
            active_only: Only return active accounts

        Returns:
            List of social accounts
        """
        query = self.db.query(SocialAccount).filter(SocialAccount.profile_id == profile_id)
        if platform:
            query = query.filter(SocialAccount.platform == platform)
        if active_only:
            query = query.filter(SocialAccount.is_active == True)
        return query.all()

    def verify_social_account(self, account_id: int) -> bool:
        """Verify social account authentication

        Args:
            account_id: Account ID

        Returns:
            True if verified
        """
        account = self.get_social_account(account_id)
        if not account:
            return False

        # Update verification status
        account.is_verified = True
        account.last_auth_at = datetime.utcnow()
        self.db.commit()
        logger.info(f"Verified social account: {account_id}")
        return True

    def get_all_active_profiles(self) -> List[Profile]:
        """Get all active profiles across all users

        Returns:
            List of active profiles
        """
        return self.db.query(Profile).filter(Profile.is_active == True).all()
