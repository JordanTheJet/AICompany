"""Engagement automation service"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from src.models.database import (
    Profile, Post, EngagementRule, EngagementAction,
    EngagementType, Platform
)
from src.integrations import TwitterIntegration, InstagramIntegration, TikTokIntegration
from datetime import datetime, timedelta
import random
import logging
import asyncio

logger = logging.getLogger(__name__)


class EngagementService:
    """Service for managing automated engagement between profiles"""

    def __init__(self, db: Session):
        """Initialize engagement service

        Args:
            db: Database session
        """
        self.db = db

    def create_engagement_rule(
        self,
        profile_id: int,
        engagement_types: List[str],
        target_profile_id: Optional[int] = None,
        like_probability: float = 0.8,
        comment_probability: float = 0.3,
        retweet_probability: float = 0.1,
        share_probability: float = 0.1,
        min_delay: int = 5,
        max_delay: int = 60,
        comment_templates: Optional[List[str]] = None,
        use_ai_comments: bool = False,
        platforms: Optional[List[str]] = None
    ) -> EngagementRule:
        """Create an engagement rule

        Args:
            profile_id: Profile that will engage
            engagement_types: Types of engagement (like, comment, retweet, share)
            target_profile_id: Target profile (None = all profiles)
            like_probability: Probability of liking (0.0-1.0)
            comment_probability: Probability of commenting (0.0-1.0)
            retweet_probability: Probability of retweeting (0.0-1.0)
            share_probability: Probability of sharing (0.0-1.0)
            min_delay: Minimum delay in minutes
            max_delay: Maximum delay in minutes
            comment_templates: List of comment templates
            use_ai_comments: Use AI to generate comments
            platforms: List of platforms to engage on

        Returns:
            Created engagement rule
        """
        rule = EngagementRule(
            profile_id=profile_id,
            target_profile_id=target_profile_id,
            engagement_types=engagement_types,
            like_probability=like_probability,
            comment_probability=comment_probability,
            retweet_probability=retweet_probability,
            share_probability=share_probability,
            min_delay=min_delay,
            max_delay=max_delay,
            comment_templates=comment_templates or [],
            use_ai_comments=use_ai_comments,
            platforms=platforms
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        logger.info(f"Created engagement rule for profile {profile_id}")
        return rule

    def get_engagement_rule(self, rule_id: int) -> Optional[EngagementRule]:
        """Get engagement rule by ID

        Args:
            rule_id: Rule ID

        Returns:
            Engagement rule or None
        """
        return self.db.query(EngagementRule).filter(EngagementRule.id == rule_id).first()

    def get_profile_engagement_rules(
        self,
        profile_id: int,
        active_only: bool = True
    ) -> List[EngagementRule]:
        """Get engagement rules for a profile

        Args:
            profile_id: Profile ID
            active_only: Only return active rules

        Returns:
            List of engagement rules
        """
        query = self.db.query(EngagementRule).filter(EngagementRule.profile_id == profile_id)
        if active_only:
            query = query.filter(EngagementRule.is_active == True)
        return query.all()

    def update_engagement_rule(self, rule_id: int, **kwargs) -> Optional[EngagementRule]:
        """Update engagement rule

        Args:
            rule_id: Rule ID
            **kwargs: Fields to update

        Returns:
            Updated rule or None
        """
        rule = self.get_engagement_rule(rule_id)
        if not rule:
            return None

        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        rule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_engagement_rule(self, rule_id: int) -> bool:
        """Delete engagement rule

        Args:
            rule_id: Rule ID

        Returns:
            True if successful
        """
        rule = self.get_engagement_rule(rule_id)
        if not rule:
            return False

        self.db.delete(rule)
        self.db.commit()
        logger.info(f"Deleted engagement rule: {rule_id}")
        return True

    def schedule_engagement_actions(
        self,
        post: Post,
        engaging_profiles: Optional[List[int]] = None
    ) -> List[EngagementAction]:
        """Schedule engagement actions for a post

        Args:
            post: Post to engage with
            engaging_profiles: List of profile IDs to engage (None = auto-detect)

        Returns:
            List of scheduled engagement actions
        """
        actions = []

        # Get profiles that should engage with this post
        if engaging_profiles:
            profiles = self.db.query(Profile).filter(
                Profile.id.in_(engaging_profiles),
                Profile.is_active == True
            ).all()
        else:
            # Get all profiles with auto-engage enabled, excluding the post author
            profiles = self.db.query(Profile).filter(
                Profile.is_active == True,
                Profile.auto_engage == True,
                Profile.id != post.profile_id
            ).all()

        for profile in profiles:
            # Get engagement rules for this profile
            rules = self.get_profile_engagement_rules(profile.id, active_only=True)

            for rule in rules:
                # Check if rule applies to this post
                if not self._rule_applies_to_post(rule, post):
                    continue

                # Schedule engagement actions based on probabilities
                scheduled_actions = self._generate_engagement_actions(
                    profile, post, rule
                )
                actions.extend(scheduled_actions)

        logger.info(f"Scheduled {len(actions)} engagement actions for post {post.id}")
        return actions

    def _rule_applies_to_post(self, rule: EngagementRule, post: Post) -> bool:
        """Check if engagement rule applies to a post

        Args:
            rule: Engagement rule
            post: Post

        Returns:
            True if rule applies
        """
        # Check target profile
        if rule.target_profile_id and rule.target_profile_id != post.profile_id:
            return False

        # Check platform filter
        if rule.platforms:
            platform_value = post.platform.value if hasattr(post.platform, 'value') else post.platform
            if platform_value not in rule.platforms:
                return False

        return True

    def _generate_engagement_actions(
        self,
        profile: Profile,
        post: Post,
        rule: EngagementRule
    ) -> List[EngagementAction]:
        """Generate engagement actions based on probabilities

        Args:
            profile: Engaging profile
            post: Post to engage with
            rule: Engagement rule

        Returns:
            List of engagement actions
        """
        actions = []
        platform = post.platform

        # Calculate delay
        delay_minutes = random.randint(rule.min_delay, rule.max_delay)
        scheduled_at = datetime.utcnow() + timedelta(minutes=delay_minutes)

        # Like
        if "like" in rule.engagement_types and random.random() < rule.like_probability:
            action = EngagementAction(
                profile_id=profile.id,
                post_id=post.id,
                engagement_type=EngagementType.LIKE,
                platform=platform,
                status="pending",
                scheduled_at=scheduled_at
            )
            self.db.add(action)
            actions.append(action)

        # Comment
        if "comment" in rule.engagement_types and random.random() < rule.comment_probability:
            comment_text = self._generate_comment(rule, post)
            if comment_text:
                # Add slight delay after like
                comment_delay = delay_minutes + random.randint(1, 5)
                comment_scheduled_at = datetime.utcnow() + timedelta(minutes=comment_delay)

                action = EngagementAction(
                    profile_id=profile.id,
                    post_id=post.id,
                    engagement_type=EngagementType.COMMENT,
                    platform=platform,
                    content=comment_text,
                    status="pending",
                    scheduled_at=comment_scheduled_at
                )
                self.db.add(action)
                actions.append(action)

        # Retweet (Twitter only)
        if (platform == Platform.TWITTER and
            "retweet" in rule.engagement_types and
            random.random() < rule.retweet_probability):

            retweet_delay = delay_minutes + random.randint(5, 15)
            retweet_scheduled_at = datetime.utcnow() + timedelta(minutes=retweet_delay)

            action = EngagementAction(
                profile_id=profile.id,
                post_id=post.id,
                engagement_type=EngagementType.RETWEET,
                platform=platform,
                status="pending",
                scheduled_at=retweet_scheduled_at
            )
            self.db.add(action)
            actions.append(action)

        if actions:
            self.db.commit()
            for action in actions:
                self.db.refresh(action)

        return actions

    def _generate_comment(self, rule: EngagementRule, post: Post) -> Optional[str]:
        """Generate a comment based on templates or AI

        Args:
            rule: Engagement rule
            post: Post

        Returns:
            Comment text or None
        """
        if rule.use_ai_comments:
            # TODO: Integrate with AI service for intelligent comments
            # For now, fall back to templates
            pass

        if rule.comment_templates:
            return random.choice(rule.comment_templates)

        # Default comments
        default_comments = [
            "Great post! 👍",
            "Love this!",
            "Interesting perspective!",
            "Thanks for sharing!",
            "This is awesome!",
            "Well said!",
            "Totally agree!",
            "Nice!",
        ]
        return random.choice(default_comments)

    def get_pending_engagement_actions(
        self,
        profile_id: Optional[int] = None,
        limit: int = 100
    ) -> List[EngagementAction]:
        """Get pending engagement actions ready to execute

        Args:
            profile_id: Filter by profile ID
            limit: Maximum number of actions

        Returns:
            List of pending actions
        """
        query = self.db.query(EngagementAction).filter(
            EngagementAction.status == "pending",
            EngagementAction.scheduled_at <= datetime.utcnow()
        )

        if profile_id:
            query = query.filter(EngagementAction.profile_id == profile_id)

        return query.order_by(EngagementAction.scheduled_at).limit(limit).all()

    async def execute_engagement_action(
        self,
        action: EngagementAction,
        social_account_credentials: Dict[str, str]
    ) -> bool:
        """Execute an engagement action

        Args:
            action: Engagement action to execute
            social_account_credentials: Credentials for the social account

        Returns:
            True if successful
        """
        try:
            platform = action.platform
            post = action.post

            if not post.platform_post_id:
                logger.error(f"Post {post.id} has no platform_post_id")
                action.status = "failed"
                action.error_message = "Post has no platform ID"
                self.db.commit()
                return False

            # Get appropriate integration
            integration = None
            if platform == Platform.TWITTER:
                integration = TwitterIntegration(credentials=social_account_credentials)
            elif platform == Platform.INSTAGRAM:
                integration = InstagramIntegration(credentials=social_account_credentials)
            elif platform == Platform.TIKTOK:
                integration = TikTokIntegration(credentials=social_account_credentials)

            if not integration:
                logger.error(f"No integration for platform {platform}")
                action.status = "failed"
                action.error_message = "Unsupported platform"
                self.db.commit()
                return False

            # Authenticate
            await integration.authenticate()

            # Execute action based on type
            if action.engagement_type == EngagementType.LIKE:
                success = await self._execute_like(integration, post.platform_post_id)

            elif action.engagement_type == EngagementType.COMMENT:
                success = await self._execute_comment(
                    integration, post.platform_post_id, action.content
                )

            elif action.engagement_type == EngagementType.RETWEET:
                success = await self._execute_retweet(integration, post.platform_post_id)

            else:
                logger.warning(f"Unsupported engagement type: {action.engagement_type}")
                success = False

            # Update action status
            if success:
                action.status = "completed"
                action.executed_at = datetime.utcnow()
                logger.info(f"Executed {action.engagement_type.value} action for post {post.id}")
            else:
                action.status = "failed"
                action.error_message = "Execution failed"

            self.db.commit()
            return success

        except Exception as e:
            logger.error(f"Error executing engagement action: {e}", exc_info=True)
            action.status = "failed"
            action.error_message = str(e)
            self.db.commit()
            return False

    async def _execute_like(self, integration: Any, post_id: str) -> bool:
        """Execute like action

        Args:
            integration: Platform integration
            post_id: Post ID on platform

        Returns:
            True if successful
        """
        try:
            if hasattr(integration, 'client_v2') and integration.client_v2:
                # Twitter
                integration.client_v2.like(post_id)
                return True
            elif hasattr(integration, 'client') and integration.client:
                # Instagram
                integration.client.media_like(post_id)
                return True
            else:
                logger.warning("Like not supported for this integration")
                return False
        except Exception as e:
            logger.error(f"Error executing like: {e}")
            return False

    async def _execute_comment(
        self,
        integration: Any,
        post_id: str,
        comment_text: str
    ) -> bool:
        """Execute comment action

        Args:
            integration: Platform integration
            post_id: Post ID on platform
            comment_text: Comment text

        Returns:
            True if successful
        """
        try:
            if hasattr(integration, 'client_v2') and integration.client_v2:
                # Twitter - reply to tweet
                integration.client_v2.create_tweet(
                    text=comment_text,
                    in_reply_to_tweet_id=post_id
                )
                return True
            elif hasattr(integration, 'client') and integration.client:
                # Instagram
                integration.client.media_comment(post_id, comment_text)
                return True
            else:
                logger.warning("Comment not supported for this integration")
                return False
        except Exception as e:
            logger.error(f"Error executing comment: {e}")
            return False

    async def _execute_retweet(self, integration: Any, post_id: str) -> bool:
        """Execute retweet action

        Args:
            integration: Platform integration
            post_id: Post ID on platform

        Returns:
            True if successful
        """
        try:
            if hasattr(integration, 'client_v2') and integration.client_v2:
                # Twitter
                integration.client_v2.retweet(post_id)
                return True
            else:
                logger.warning("Retweet not supported for this platform")
                return False
        except Exception as e:
            logger.error(f"Error executing retweet: {e}")
            return False
