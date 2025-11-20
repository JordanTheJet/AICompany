"""Engagement automation API routes"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from src.database import get_db
from src.services import EngagementService, PostService, ProfileService
from src.models.database import EngagementAction

router = APIRouter(prefix="/engagement", tags=["Engagement"])


# Request/Response Models
class EngagementRuleCreate(BaseModel):
    """Engagement rule creation request"""
    profile_id: int
    target_profile_id: Optional[int] = None
    engagement_types: List[str]  # ["like", "comment", "retweet", "share"]
    like_probability: float = 0.8
    comment_probability: float = 0.3
    retweet_probability: float = 0.1
    share_probability: float = 0.1
    min_delay: int = 5
    max_delay: int = 60
    comment_templates: Optional[List[str]] = None
    use_ai_comments: bool = False
    platforms: Optional[List[str]] = None


class EngagementRuleResponse(BaseModel):
    """Engagement rule response"""
    id: int
    profile_id: int
    target_profile_id: Optional[int]
    is_active: bool
    engagement_types: List[str]
    like_probability: float
    comment_probability: float
    min_delay: int
    max_delay: int

    class Config:
        from_attributes = True


class EngagementActionResponse(BaseModel):
    """Engagement action response"""
    id: int
    profile_id: int
    post_id: int
    engagement_type: str
    platform: str
    status: str
    scheduled_at: Optional[Any]
    executed_at: Optional[Any]

    class Config:
        from_attributes = True


class ExecuteEngagementRequest(BaseModel):
    """Execute pending engagement actions request"""
    profile_id: Optional[int] = None
    limit: int = 100


# Endpoints
@router.post("/rules", response_model=EngagementRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_engagement_rule(
    rule: EngagementRuleCreate,
    db: Session = Depends(get_db)
):
    """Create an engagement rule

    This rule defines how a profile will automatically engage with posts
    from other profiles. You can set probabilities for different types
    of engagement (likes, comments, retweets) and customize timing.
    """
    service = EngagementService(db)
    profile_service = ProfileService(db)

    # Verify profile exists
    profile = profile_service.get_profile(rule.profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Verify target profile exists if specified
    if rule.target_profile_id:
        target_profile = profile_service.get_profile(rule.target_profile_id)
        if not target_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target profile not found"
            )

    created_rule = service.create_engagement_rule(
        profile_id=rule.profile_id,
        engagement_types=rule.engagement_types,
        target_profile_id=rule.target_profile_id,
        like_probability=rule.like_probability,
        comment_probability=rule.comment_probability,
        retweet_probability=rule.retweet_probability,
        share_probability=rule.share_probability,
        min_delay=rule.min_delay,
        max_delay=rule.max_delay,
        comment_templates=rule.comment_templates,
        use_ai_comments=rule.use_ai_comments,
        platforms=rule.platforms
    )
    return created_rule


@router.get("/rules/profile/{profile_id}", response_model=List[EngagementRuleResponse])
async def get_profile_engagement_rules(
    profile_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get engagement rules for a profile"""
    service = EngagementService(db)
    rules = service.get_profile_engagement_rules(profile_id, active_only=active_only)
    return rules


@router.get("/rules/{rule_id}", response_model=EngagementRuleResponse)
async def get_engagement_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get engagement rule by ID"""
    service = EngagementService(db)
    rule = service.get_engagement_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement rule not found"
        )
    return rule


@router.put("/rules/{rule_id}", response_model=EngagementRuleResponse)
async def update_engagement_rule(
    rule_id: int,
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update engagement rule"""
    service = EngagementService(db)
    rule = service.update_engagement_rule(rule_id, **updates)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement rule not found"
        )
    return rule


@router.delete("/rules/{rule_id}")
async def delete_engagement_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete engagement rule"""
    service = EngagementService(db)
    success = service.delete_engagement_rule(rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engagement rule not found"
        )
    return {"success": True, "message": "Engagement rule deleted"}


@router.get("/actions/pending", response_model=List[EngagementActionResponse])
async def get_pending_engagement_actions(
    profile_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get pending engagement actions ready to execute"""
    service = EngagementService(db)
    actions = service.get_pending_engagement_actions(
        profile_id=profile_id,
        limit=limit
    )
    return actions


@router.post("/actions/execute")
async def execute_pending_engagement_actions(
    request: ExecuteEngagementRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Execute pending engagement actions

    This endpoint processes all pending engagement actions that are
    scheduled to run. It's designed to be called by a scheduler or
    manually triggered.
    """
    service = EngagementService(db)
    profile_service = ProfileService(db)

    # Get pending actions
    actions = service.get_pending_engagement_actions(
        profile_id=request.profile_id,
        limit=request.limit
    )

    executed_count = 0
    failed_count = 0

    for action in actions:
        try:
            # Get social account credentials for the engaging profile
            profile = profile_service.get_profile(action.profile_id)
            if not profile:
                continue

            accounts = profile_service.get_profile_social_accounts(
                profile_id=action.profile_id,
                platform=action.platform,
                active_only=True
            )

            if not accounts:
                action.status = "failed"
                action.error_message = "No active social account found"
                db.commit()
                failed_count += 1
                continue

            social_account = accounts[0]

            # Execute in background
            background_tasks.add_task(
                execute_single_engagement_action,
                action.id,
                social_account.credentials,
                db
            )
            executed_count += 1

        except Exception as e:
            print(f"Error executing engagement action {action.id}: {e}")
            failed_count += 1

    return {
        "success": True,
        "executed_count": executed_count,
        "failed_count": failed_count,
        "message": f"Executing {executed_count} engagement actions"
    }


async def execute_single_engagement_action(
    action_id: int,
    credentials: Dict[str, str],
    db: Session
):
    """Background task to execute a single engagement action"""
    try:
        service = EngagementService(db)
        action = db.query(EngagementAction).filter(EngagementAction.id == action_id).first()
        if action:
            await service.execute_engagement_action(action, credentials)
    except Exception as e:
        print(f"Error in background execution: {e}")


@router.post("/posts/{post_id}/schedule")
async def schedule_engagement_for_post(
    post_id: int,
    engaging_profiles: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """Manually schedule engagement actions for a specific post

    This allows you to trigger engagement automation for a specific post,
    optionally specifying which profiles should engage.
    """
    service = EngagementService(db)
    post_service = PostService(db)

    # Verify post exists
    post = post_service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Schedule engagement actions
    actions = service.schedule_engagement_actions(
        post=post,
        engaging_profiles=engaging_profiles
    )

    return {
        "success": True,
        "post_id": post_id,
        "scheduled_actions": len(actions),
        "message": f"Scheduled {len(actions)} engagement actions for post"
    }


@router.get("/stats/profile/{profile_id}")
async def get_profile_engagement_stats(
    profile_id: int,
    db: Session = Depends(get_db)
):
    """Get engagement statistics for a profile

    Returns stats on how many engagement actions this profile
    has performed and received.
    """
    # Get engagement actions by this profile
    performed_actions = db.query(EngagementAction).filter(
        EngagementAction.profile_id == profile_id
    ).all()

    # Get posts by this profile
    post_service = PostService(db)
    profile_posts = post_service.get_profile_posts(profile_id, limit=1000)

    # Get engagement actions on this profile's posts
    post_ids = [post.id for post in profile_posts]
    received_actions = db.query(EngagementAction).filter(
        EngagementAction.post_id.in_(post_ids)
    ).all() if post_ids else []

    # Calculate stats
    stats = {
        "profile_id": profile_id,
        "engagement_performed": {
            "total": len(performed_actions),
            "completed": len([a for a in performed_actions if a.status == "completed"]),
            "pending": len([a for a in performed_actions if a.status == "pending"]),
            "failed": len([a for a in performed_actions if a.status == "failed"]),
            "by_type": {}
        },
        "engagement_received": {
            "total": len(received_actions),
            "completed": len([a for a in received_actions if a.status == "completed"]),
            "by_type": {}
        },
        "posts_count": len(profile_posts),
        "total_likes_received": sum(post.like_count for post in profile_posts),
        "total_comments_received": sum(post.comment_count for post in profile_posts)
    }

    # Count by type
    for action in performed_actions:
        action_type = action.engagement_type.value
        stats["engagement_performed"]["by_type"][action_type] = \
            stats["engagement_performed"]["by_type"].get(action_type, 0) + 1

    for action in received_actions:
        action_type = action.engagement_type.value
        stats["engagement_received"]["by_type"][action_type] = \
            stats["engagement_received"]["by_type"].get(action_type, 0) + 1

    return stats
