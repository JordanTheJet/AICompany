"""Background scheduler for automated engagement tasks"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.database import SessionLocal
from src.services import EngagementService, ProfileService
import signal
import sys

logger = logging.getLogger(__name__)


class EngagementScheduler:
    """Scheduler for automated engagement tasks"""

    def __init__(self, interval_minutes: int = 5):
        """Initialize scheduler

        Args:
            interval_minutes: Interval between engagement runs in minutes
        """
        self.scheduler = AsyncIOScheduler()
        self.interval_minutes = interval_minutes
        self.running = False

    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        logger.info(f"Starting engagement scheduler (interval: {self.interval_minutes} minutes)")

        # Add job to run engagement processing
        self.scheduler.add_job(
            self.process_pending_engagement,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="engagement_processor",
            name="Process pending engagement actions",
            replace_existing=True
        )

        # Add job to check scheduled posts
        self.scheduler.add_job(
            self.process_scheduled_posts,
            trigger=IntervalTrigger(minutes=1),
            id="scheduled_posts_processor",
            name="Process scheduled posts",
            replace_existing=True
        )

        self.scheduler.start()
        self.running = True
        logger.info("Engagement scheduler started successfully")

    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return

        logger.info("Stopping engagement scheduler...")
        self.scheduler.shutdown()
        self.running = False
        logger.info("Engagement scheduler stopped")

    async def process_pending_engagement(self):
        """Process pending engagement actions"""
        logger.info("Processing pending engagement actions...")
        db = SessionLocal()

        try:
            engagement_service = EngagementService(db)
            profile_service = ProfileService(db)

            # Get all pending actions
            actions = engagement_service.get_pending_engagement_actions(limit=100)

            logger.info(f"Found {len(actions)} pending engagement actions")

            for action in actions:
                try:
                    # Get social account credentials
                    accounts = profile_service.get_profile_social_accounts(
                        profile_id=action.profile_id,
                        platform=action.platform,
                        active_only=True
                    )

                    if not accounts:
                        logger.warning(f"No active account for profile {action.profile_id} on {action.platform}")
                        action.status = "failed"
                        action.error_message = "No active social account"
                        db.commit()
                        continue

                    social_account = accounts[0]

                    # Execute engagement action
                    success = await engagement_service.execute_engagement_action(
                        action,
                        social_account.credentials
                    )

                    if success:
                        logger.info(f"Successfully executed {action.engagement_type.value} action {action.id}")
                    else:
                        logger.error(f"Failed to execute engagement action {action.id}")

                    # Add small delay between actions to avoid rate limiting
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"Error processing engagement action {action.id}: {e}", exc_info=True)
                    action.status = "failed"
                    action.error_message = str(e)
                    db.commit()

        except Exception as e:
            logger.error(f"Error in engagement processing: {e}", exc_info=True)
        finally:
            db.close()

        logger.info("Engagement processing complete")

    async def process_scheduled_posts(self):
        """Process scheduled posts that are due to be published"""
        logger.debug("Checking for scheduled posts...")
        db = SessionLocal()

        try:
            from src.services import PostService
            from src.models.database import Post, PostStatus

            # Get posts scheduled to be published now
            due_posts = db.query(Post).filter(
                Post.status == PostStatus.SCHEDULED,
                Post.scheduled_at <= datetime.utcnow()
            ).limit(50).all()

            if due_posts:
                logger.info(f"Found {len(due_posts)} posts due for publishing")

            for post in due_posts:
                try:
                    # TODO: Implement post publishing logic
                    logger.info(f"Publishing scheduled post {post.id}")
                    # This would integrate with the post publishing endpoint
                except Exception as e:
                    logger.error(f"Error publishing post {post.id}: {e}")

        except Exception as e:
            logger.error(f"Error processing scheduled posts: {e}", exc_info=True)
        finally:
            db.close()


# Global scheduler instance
_scheduler: Optional[EngagementScheduler] = None


def get_scheduler() -> EngagementScheduler:
    """Get global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = EngagementScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()


async def run_scheduler_standalone():
    """Run scheduler as standalone process"""
    logger.info("Starting AICompany Engagement Scheduler")

    scheduler = get_scheduler()
    scheduler.start()

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        scheduler.stop()


if __name__ == "__main__":
    # Run scheduler standalone
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(run_scheduler_standalone())
