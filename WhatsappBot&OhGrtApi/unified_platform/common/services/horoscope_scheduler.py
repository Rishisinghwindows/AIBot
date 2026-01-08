"""
Daily Horoscope Scheduler

Sends personalized daily horoscope messages to subscribed users.

Features:
- Scheduled delivery at user's preferred time
- Personalized based on birth chart (if available)
- Multi-language support
- Transit-aware daily insights
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, date

from common.services.subscription_service import (
    get_subscription_service,
    SubscriptionType,
    Subscription
)
from common.tools.astro_tool import get_horoscope
from common.i18n import get_translator

logger = logging.getLogger(__name__)


class HoroscopeScheduler:
    """
    Schedules and sends daily horoscope notifications.

    Usage:
        scheduler = get_horoscope_scheduler()
        await scheduler.start()  # Starts background task

        # Or manually trigger for testing
        await scheduler.send_daily_horoscopes()
    """

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler background task."""
        if self._running:
            logger.warning("Horoscope scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Horoscope scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Horoscope scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop - runs every minute."""
        while self._running:
            try:
                # Check every minute
                await asyncio.sleep(60)

                # Get current time
                current_time = datetime.now().strftime("%H:%M")

                # Process due subscribers
                await self._process_due_subscribers(current_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retry

    async def _process_due_subscribers(self, current_time: str):
        """Process subscribers who should receive horoscope now."""
        service = get_subscription_service()

        # Get subscribers due at this time
        due_subscribers = await service.get_due_subscribers(
            SubscriptionType.DAILY_HOROSCOPE,
            target_time=current_time
        )

        if not due_subscribers:
            return

        logger.info(f"Processing {len(due_subscribers)} horoscope notifications at {current_time}")

        for subscription in due_subscribers:
            try:
                await self._send_horoscope(subscription)
                await service.update_last_sent(
                    subscription.phone,
                    SubscriptionType.DAILY_HOROSCOPE
                )
            except Exception as e:
                logger.error(f"Error sending horoscope to {subscription.phone}: {e}")

    async def _send_horoscope(self, subscription: Subscription):
        """Generate and send horoscope to a subscriber."""
        phone = subscription.phone
        zodiac_sign = subscription.zodiac_sign

        if not zodiac_sign:
            logger.warning(f"No zodiac sign for subscriber {phone}")
            return

        # Get user's language preference
        from common.stores import get_store
        store = get_store()
        user = await store.get_user(phone)
        lang = user.preferred_language if user else "en"

        # Generate horoscope
        result = await get_horoscope(zodiac_sign, period="today")

        if not result.get("success"):
            logger.error(f"Failed to generate horoscope for {zodiac_sign}")
            return

        # Format message
        message = self._format_horoscope_message(
            result["data"],
            zodiac_sign,
            lang,
            user
        )

        # Send via WhatsApp
        await self._send_whatsapp_message(phone, message)

        logger.info(f"Sent daily horoscope to {phone}")

    def _format_horoscope_message(
        self,
        horoscope_data: dict,
        zodiac_sign: str,
        lang: str,
        user=None
    ) -> str:
        """Format horoscope data into a WhatsApp message."""
        translator = get_translator()

        # Get translated zodiac name
        sign_name = translator.get_zodiac_name(zodiac_sign, lang)

        # Build message
        today = date.today().strftime("%d %B %Y")

        lines = [
            f"🌟 *Daily Horoscope*",
            f"*{sign_name}* - {today}",
            "",
        ]

        # Overall prediction
        overall = horoscope_data.get("overall", horoscope_data.get("prediction", ""))
        if overall:
            lines.append(overall)
            lines.append("")

        # Category predictions
        categories = [
            ("love", "❤️ Love"),
            ("career", "💼 Career"),
            ("health", "🏃 Health"),
            ("finance", "💰 Finance"),
        ]

        for key, label in categories:
            if key in horoscope_data and horoscope_data[key]:
                lines.append(f"{label}: {horoscope_data[key]}")

        lines.append("")

        # Lucky elements
        lucky_elements = []
        if horoscope_data.get("lucky_number"):
            lucky_elements.append(f"🔢 {horoscope_data['lucky_number']}")
        if horoscope_data.get("lucky_color"):
            lucky_elements.append(f"🎨 {horoscope_data['lucky_color']}")

        if lucky_elements:
            lines.append("*Lucky:* " + " | ".join(lucky_elements))

        # Add personalized insight if user has birth details
        if user and user.has_birth_details() and user.moon_nakshatra:
            lines.append("")
            lines.append(f"_Based on your Moon in {user.moon_nakshatra}_")

        # Footer
        lines.append("")
        lines.append("_Reply 'stop horoscope' to unsubscribe_")

        return "\n".join(lines)

    async def _send_whatsapp_message(self, phone: str, message: str):
        """Send message via WhatsApp Cloud API."""
        from common.whatsapp.client import send_text_message

        try:
            await send_text_message(phone, message)
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {phone}: {e}")
            raise

    async def send_daily_horoscopes(self):
        """
        Manually trigger sending horoscopes to all due subscribers.
        Useful for testing or manual triggers.
        """
        current_time = datetime.now().strftime("%H:%M")
        await self._process_due_subscribers(current_time)

    async def send_test_horoscope(self, phone: str, zodiac_sign: str):
        """
        Send a test horoscope to a specific phone number.

        Args:
            phone: Phone number to send to
            zodiac_sign: Zodiac sign for horoscope
        """
        subscription = Subscription(
            phone=phone,
            subscription_type=SubscriptionType.DAILY_HOROSCOPE,
            zodiac_sign=zodiac_sign
        )
        await self._send_horoscope(subscription)


# =============================================================================
# SINGLETON
# =============================================================================

_horoscope_scheduler: Optional[HoroscopeScheduler] = None


def get_horoscope_scheduler() -> HoroscopeScheduler:
    """Get singleton HoroscopeScheduler instance."""
    global _horoscope_scheduler
    if _horoscope_scheduler is None:
        _horoscope_scheduler = HoroscopeScheduler()
    return _horoscope_scheduler


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def start_horoscope_scheduler():
    """Start the horoscope scheduler."""
    scheduler = get_horoscope_scheduler()
    await scheduler.start()


async def stop_horoscope_scheduler():
    """Stop the horoscope scheduler."""
    scheduler = get_horoscope_scheduler()
    await scheduler.stop()
