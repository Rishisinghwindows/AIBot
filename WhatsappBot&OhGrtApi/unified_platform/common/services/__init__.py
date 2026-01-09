"""
Bot Services

Background services for:
- Scheduled notifications (horoscope, alerts)
- Transit monitoring
- Subscription management
- Reminders
"""

from common.services.subscription_service import (
    get_subscription_service,
    SubscriptionService,
    SubscriptionType,
    Subscription,
)

from common.services.horoscope_scheduler import (
    get_horoscope_scheduler,
    HoroscopeScheduler,
    start_horoscope_scheduler,
    stop_horoscope_scheduler,
)

from common.services.transit_service import (
    get_transit_service,
    TransitService,
    TransitEvent,
    TransitEventType,
    start_transit_service,
    stop_transit_service,
)

# Import reminder service if it exists
try:
    from common.services.reminder_service import (
        ReminderService,
        get_reminder_service,
    )
except ImportError:
    ReminderService = None
    get_reminder_service = None

# Import TTS service
try:
    from common.services.tts_service import (
        TTSService,
        get_tts_service,
    )
except ImportError:
    TTSService = None
    get_tts_service = None

# Import Chat Processor
try:
    from common.services.chat_processor import (
        CommonChatProcessor,
        get_chat_processor,
    )
except ImportError:
    CommonChatProcessor = None
    get_chat_processor = None

# Import AI Language Service
try:
    from common.services.ai_language_service import (
        AILanguageService,
        get_ai_language_service,
        init_ai_language_service,
        ai_understand_message,
        ai_translate_response,
    )
except ImportError:
    AILanguageService = None
    get_ai_language_service = None
    init_ai_language_service = None
    ai_understand_message = None
    ai_translate_response = None


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

    # Chat Processor
    "CommonChatProcessor",
    "get_chat_processor",

    # AI Language Service
    "AILanguageService",
    "get_ai_language_service",
    "init_ai_language_service",
    "ai_understand_message",
    "ai_translate_response",
]


async def start_all_services():
    """Start all background services."""
    await start_horoscope_scheduler()
    await start_transit_service()


async def stop_all_services():
    """Stop all background services."""
    await stop_horoscope_scheduler()
    await stop_transit_service()
