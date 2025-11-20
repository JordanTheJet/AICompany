"""Profile management API routes"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from src.database import get_db
from src.services import ProfileService
from src.models.database import Platform

router = APIRouter(prefix="/profiles", tags=["Profiles"])


# Request/Response Models
class UserCreate(BaseModel):
    """User creation request"""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response"""
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class ProfileCreate(BaseModel):
    """Profile creation request"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    auto_engage: bool = False
    engagement_delay_min: int = 5
    engagement_delay_max: int = 60
    metadata: Optional[Dict[str, Any]] = None


class ProfileResponse(BaseModel):
    """Profile response"""
    id: int
    user_id: int
    name: str
    display_name: str
    description: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    auto_engage: bool
    engagement_delay_min: int
    engagement_delay_max: int

    class Config:
        from_attributes = True


class SocialAccountCreate(BaseModel):
    """Social account creation request"""
    platform: str
    credentials: Dict[str, str]
    platform_username: Optional[str] = None
    platform_user_id: Optional[str] = None
    platform_display_name: Optional[str] = None


class SocialAccountResponse(BaseModel):
    """Social account response"""
    id: int
    profile_id: int
    platform: str
    platform_username: Optional[str]
    platform_display_name: Optional[str]
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


# User Endpoints
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    service = ProfileService(db)

    # Check if user already exists
    existing = service.get_user_by_username(user.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    created_user = service.create_user(
        email=user.email,
        username=user.username,
        password=user.password,
        full_name=user.full_name
    )
    return created_user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    service = ProfileService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


# Profile Endpoints
@router.post("/users/{user_id}/profiles", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    user_id: int,
    profile: ProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new profile for a user"""
    service = ProfileService(db)

    # Verify user exists
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    created_profile = service.create_profile(
        user_id=user_id,
        name=profile.name,
        display_name=profile.display_name,
        description=profile.description,
        avatar_url=profile.avatar_url,
        auto_engage=profile.auto_engage,
        engagement_delay_min=profile.engagement_delay_min,
        engagement_delay_max=profile.engagement_delay_max,
        metadata=profile.metadata
    )
    return created_profile


@router.get("/users/{user_id}/profiles", response_model=List[ProfileResponse])
async def get_user_profiles(
    user_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all profiles for a user"""
    service = ProfileService(db)
    profiles = service.get_user_profiles(user_id, active_only=active_only)
    return profiles


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """Get profile by ID"""
    service = ProfileService(db)
    profile = service.get_profile(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: int,
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update profile"""
    service = ProfileService(db)
    profile = service.update_profile(profile_id, **updates)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile


@router.delete("/{profile_id}")
async def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete profile (soft delete)"""
    service = ProfileService(db)
    success = service.delete_profile(profile_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return {"success": True, "message": "Profile deleted"}


# Social Account Endpoints
@router.post("/{profile_id}/social-accounts", response_model=SocialAccountResponse, status_code=status.HTTP_201_CREATED)
async def add_social_account(
    profile_id: int,
    account: SocialAccountCreate,
    db: Session = Depends(get_db)
):
    """Add a social account to a profile"""
    service = ProfileService(db)

    # Verify profile exists
    profile = service.get_profile(profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Convert platform string to enum
    try:
        platform = Platform[account.platform.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {account.platform}"
        )

    created_account = service.add_social_account(
        profile_id=profile_id,
        platform=platform,
        credentials=account.credentials,
        platform_username=account.platform_username,
        platform_user_id=account.platform_user_id,
        platform_display_name=account.platform_display_name
    )
    return created_account


@router.get("/{profile_id}/social-accounts", response_model=List[SocialAccountResponse])
async def get_profile_social_accounts(
    profile_id: int,
    platform: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get social accounts for a profile"""
    service = ProfileService(db)

    platform_enum = None
    if platform:
        try:
            platform_enum = Platform[platform.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform}"
            )

    accounts = service.get_profile_social_accounts(
        profile_id=profile_id,
        platform=platform_enum,
        active_only=active_only
    )
    return accounts


@router.post("/social-accounts/{account_id}/verify")
async def verify_social_account(account_id: int, db: Session = Depends(get_db)):
    """Verify social account authentication"""
    service = ProfileService(db)
    success = service.verify_social_account(account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found"
        )
    return {"success": True, "message": "Account verified"}


@router.get("/all/active", response_model=List[ProfileResponse])
async def get_all_active_profiles(db: Session = Depends(get_db)):
    """Get all active profiles across all users"""
    service = ProfileService(db)
    profiles = service.get_all_active_profiles()
    return profiles
