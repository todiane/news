# backend/app/core/notification_manager.py

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List, Dict, Any
from datetime import datetime
import logging
from app.core.config import settings
from app.models.feed_preference import FeedPreference
from app.models.user import User

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.mail_config = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_SSL_TLS=True,
            MAIL_STARTTLS=getattr(settings, "MAIL_STARTTLS", False),  # Use default if not set
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            USE_CREDENTIALS=True
        )
        self.fastmail = FastMail(self.mail_config)

    async def notify_feed_updates(self, user: User, feed_id: int, updates: List[Dict[str, Any]]):
        """Send notification about new feed updates."""
        if not updates:
            return
        
        pref = await self._get_user_preference(user.id, feed_id)
        if not pref or not pref.notification_enabled:
            return

        # Check update frequency
        if not self._should_send_notification(pref):
            return

        # Prepare email content
        content = self._format_update_content(updates)
        
        message = MessageSchema(
            subject=f"New updates from {updates[0]['feed_name']}",
            recipients=[user.email],
            body=content,
            subtype="html"
        )

        try:
            await self.fastmail.send_message(message)
            logger.info(f"Sent notification to {user.email} for feed {feed_id}")
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")

    def _should_send_notification(self, pref: FeedPreference) -> bool:
        """Check if notification should be sent based on frequency settings."""
        if pref.update_frequency == "realtime":
            return True

        last_notified = getattr(pref, 'last_notification_sent', None)
        if not last_notified:
            return True

        now = datetime.utcnow()
        time_diff = now - last_notified

        if pref.update_frequency == "hourly" and time_diff.total_seconds() < 3600:
            return False
        elif pref.update_frequency == "daily" and time_diff.total_seconds() < 86400:
            return False
        elif pref.update_frequency == "weekly" and time_diff.total_seconds() < 604800:
            return False

        return True

    def _format_update_content(self, updates: List[Dict[str, Any]]) -> str:
        """Format updates into HTML email content."""
        html_content = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">New Updates</h2>
            <div style="margin-top: 20px;">
        """

        for update in updates:
            html_content += f"""
                <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #e1e1e1; border-radius: 5px;">
                    <h3 style="margin: 0; color: #2c3e50;">{update['title']}</h3>
                    <p style="color: #666; margin: 10px 0;">{update['summary'][:200]}...</p>
                    <a href="{update['url']}" 
                       style="color: #3498db; text-decoration: none;">Read more →</a>
                </div>
            """

        html_content += """
            </div>
        </div>
        """
        return html_content

notification_manager = NotificationManager()
