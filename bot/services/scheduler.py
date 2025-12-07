import logging
from datetime import datetime

import pytz
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.database import UserRepository, async_session
from bot.services.iqair import iqair_service

logger = logging.getLogger(__name__)

ALMATY_TZ = pytz.timezone("Asia/Almaty")


def get_greeting(hour: int) -> str:
    """Return appropriate greeting based on hour"""
    if 5 <= hour < 12:
        return "🌅 Доброе утро!"
    elif 12 <= hour < 18:
        return "🌤 Добрый день!"
    elif 18 <= hour < 23:
        return "🌆 Добрый вечер!"
    else:
        return "🌙 Доброй ночи!"


class NotificationScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=ALMATY_TZ)
        self._last_aqi: int | None = None

    def start(self) -> None:
        # Check for daily notifications every minute
        self.scheduler.add_job(
            self._send_daily_notifications,
            "cron",
            minute="*",
            id="daily_notifications",
        )

        # Check AQI for alerts every 15 minutes
        self.scheduler.add_job(
            self._check_aqi_alerts,
            "interval",
            minutes=15,
            id="aqi_alerts",
        )

        self.scheduler.start()
        logger.info("Notification scheduler started")

    def stop(self) -> None:
        self.scheduler.shutdown()
        logger.info("Notification scheduler stopped")

    async def _send_daily_notifications(self) -> None:
        """Send daily notifications to users whose scheduled time matches current time"""
        now = datetime.now(ALMATY_TZ)
        current_hour = now.hour
        current_minute = now.minute

        logger.debug(f"Checking daily notifications for {current_hour:02d}:{current_minute:02d}")

        async with async_session() as session:
            repo = UserRepository(session)
            users = await repo.get_users_for_daily_notification(current_hour, current_minute)

            if not users:
                return

            # Get current air quality
            air_data = await iqair_service.get_air_quality()
            if not air_data:
                logger.warning("Could not fetch air quality data for daily notifications")
                return

            message = air_data.format_message()

            greeting = get_greeting(current_hour)
            for user in users:
                try:
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=f"<b>{greeting}</b>\n\n{message}",
                        parse_mode="HTML",
                    )
                    logger.info(f"Sent daily notification to user {user.telegram_id}")
                except Exception as e:
                    logger.error(f"Failed to send notification to {user.telegram_id}: {e}")

    async def _check_aqi_alerts(self) -> None:
        """Check AQI and send alerts if threshold exceeded or quality improved"""
        air_data = await iqair_service.get_air_quality(force_refresh=True)
        if not air_data:
            logger.warning("Could not fetch air quality data for alerts")
            return

        current_aqi = air_data.aqi
        logger.debug(f"Current AQI: {current_aqi}")

        async with async_session() as session:
            repo = UserRepository(session)
            users = await repo.get_users_for_alert()

            for user in users:
                await self._process_user_alert(user, current_aqi, air_data, repo)

        self._last_aqi = current_aqi

    async def _process_user_alert(self, user, current_aqi: int, air_data, repo: UserRepository) -> None:
        """Process alert for a single user"""
        threshold = user.alert_threshold
        last_level = user.last_aqi_level

        # Determine current level category
        if current_aqi >= 301:
            current_level = "hazardous"
        elif current_aqi >= 201:
            current_level = "very_unhealthy"
        elif current_aqi >= 151:
            current_level = "unhealthy"
        elif current_aqi >= 101:
            current_level = "unhealthy_sensitive"
        else:
            current_level = "good"

        # Check if we should send an alert
        should_alert = False
        alert_type = None

        if current_aqi >= threshold:
            # AQI exceeded threshold
            if last_level != current_level:
                should_alert = True
                alert_type = "warning"
        elif last_level in ("unhealthy_sensitive", "unhealthy", "very_unhealthy", "hazardous"):
            # AQI improved from bad to good
            if current_aqi < threshold:
                should_alert = True
                alert_type = "improved"

        if should_alert:
            try:
                if alert_type == "warning":
                    prefix = "⚠️ <b>Внимание! Качество воздуха ухудшилось</b>\n\n"
                else:
                    prefix = "✅ <b>Качество воздуха улучшилось!</b>\n\n"

                await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"{prefix}{air_data.format_message()}",
                    parse_mode="HTML",
                )
                logger.info(f"Sent {alert_type} alert to user {user.telegram_id}")
            except Exception as e:
                logger.error(f"Failed to send alert to {user.telegram_id}: {e}")

        # Update user's last AQI level
        await repo.update_last_aqi_level(user.telegram_id, current_level)
