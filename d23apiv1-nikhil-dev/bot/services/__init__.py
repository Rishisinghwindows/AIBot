"""
Bot Services

Background services for:
- Scheduled notifications (horoscope, alerts)
- Transit monitoring
- Subscription management
- Reminders
"""

from bot.services.subscription_service import (
    get_subscription_service,
    SubscriptionService,
    SubscriptionType,
    Subscription,
)

from bot.services.horoscope_scheduler import (
    get_horoscope_scheduler,
    HoroscopeScheduler,
    start_horoscope_scheduler,
    stop_horoscope_scheduler,
)

from bot.services.transit_service import (
    get_transit_service,
    TransitService,
    TransitEvent,
    TransitEventType,
    start_transit_service,
    stop_transit_service,
)

# Import reminder service if it exists
try:
    from bot.services.reminder_service import (
        ReminderService,
        get_reminder_service,
    )
except ImportError:
    ReminderService = None
    get_reminder_service = None

# Import TTS service
try:
    from bot.services.tts_service import (
        TTSService,
        get_tts_service,
    )
except ImportError:
    TTSService = None
    get_tts_service = None


__all__ = [
    # Subscription
    "get_subscription_service",
    "SubscriptionService",
    "SubscriptionType",
    "Subscription",

    # Horoscope Scheduler
    "get_horoscope_scheduler",
    "HoroscopeScheduler",
    "start_horoscope_scheduler",
    "stop_horoscope_scheduler",

    # Transit Service
    "get_transit_service",
    "TransitService",
    "TransitEvent",
    "TransitEventType",
    "start_transit_service",
    "stop_transit_service",

    # Reminder
    "ReminderService",
    "get_reminder_service",

    # TTS
    "TTSService",
    "get_tts_service",
]


async def start_all_services():
    """Start all background services."""
    await start_horoscope_scheduler()
    await start_transit_service()


async def stop_all_services():
    """Stop all background services."""
    await stop_horoscope_scheduler()
    await stop_transit_service()
