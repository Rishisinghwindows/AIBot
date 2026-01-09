"""
Transit Alert Service

Monitors planetary transits and sends personalized alerts to users.

Features:
- Track major planetary movements (Saturn, Jupiter, Rahu, Ketu)
- Detect sign/house changes
- Retrograde alerts
- Personalized impact based on user's birth chart
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

from common.services.subscription_service import (
    get_subscription_service,
    SubscriptionType,
    Subscription
)

logger = logging.getLogger(__name__)


class TransitEventType(Enum):
    """Types of transit events to track."""
    SIGN_CHANGE = "sign_change"           # Planet enters new sign
    HOUSE_TRANSIT = "house_transit"       # Planet transits user's house
    RETROGRADE_START = "retrograde_start"  # Planet goes retrograde
    RETROGRADE_END = "retrograde_end"      # Planet goes direct
    CONJUNCTION = "conjunction"            # Two planets conjunct
    ASPECT = "aspect"                      # Major aspect formation


@dataclass
class TransitEvent:
    """Represents a transit event."""
    event_type: TransitEventType
    planet: str
    from_sign: Optional[str] = None
    to_sign: Optional[str] = None
    event_date: Optional[date] = None
    description: str = ""
    impact_level: str = "medium"  # low, medium, high
    affected_houses: List[int] = None

    def __post_init__(self):
        if self.affected_houses is None:
            self.affected_houses = []


# =============================================================================
# PLANETARY DATA (2024-2025)
# =============================================================================

# Major planetary transits for 2024-2025
# In production, this would come from ephemeris calculations
UPCOMING_TRANSITS = [
    TransitEvent(
        event_type=TransitEventType.SIGN_CHANGE,
        planet="jupiter",
        from_sign="aries",
        to_sign="taurus",
        event_date=date(2024, 5, 1),
        description="Jupiter enters Taurus - expansion in finances and values",
        impact_level="high"
    ),
    TransitEvent(
        event_type=TransitEventType.SIGN_CHANGE,
        planet="saturn",
        from_sign="aquarius",
        to_sign="pisces",
        event_date=date(2024, 3, 29),
        description="Saturn enters Pisces - restructuring of beliefs and spirituality",
        impact_level="high"
    ),
    TransitEvent(
        event_type=TransitEventType.RETROGRADE_START,
        planet="mercury",
        from_sign="aries",
        to_sign="aries",
        event_date=date(2024, 4, 1),
        description="Mercury retrograde in Aries - communication delays, revisit past decisions",
        impact_level="medium"
    ),
    TransitEvent(
        event_type=TransitEventType.SIGN_CHANGE,
        planet="rahu",
        from_sign="aries",
        to_sign="pisces",
        event_date=date(2025, 1, 29),
        description="Rahu enters Pisces - new karmic lessons in spirituality",
        impact_level="high"
    ),
    TransitEvent(
        event_type=TransitEventType.SIGN_CHANGE,
        planet="ketu",
        from_sign="libra",
        to_sign="virgo",
        event_date=date(2025, 1, 29),
        description="Ketu enters Virgo - letting go of perfectionism",
        impact_level="high"
    ),
]

# Retrograde periods for 2024
RETROGRADE_PERIODS = {
    "mercury": [
        (date(2024, 4, 1), date(2024, 4, 25)),
        (date(2024, 8, 5), date(2024, 8, 28)),
        (date(2024, 11, 25), date(2024, 12, 15)),
    ],
    "venus": [
        (date(2024, 7, 22), date(2024, 9, 3)),
    ],
    "mars": [
        (date(2024, 12, 6), date(2025, 2, 23)),
    ],
    "jupiter": [
        (date(2024, 10, 9), date(2025, 2, 4)),
    ],
    "saturn": [
        (date(2024, 6, 29), date(2024, 11, 15)),
    ],
}

# Sign order for calculating house transits
SIGNS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces"
]


class TransitService:
    """
    Monitors and alerts users about planetary transits.

    Usage:
        service = get_transit_service()
        await service.start()  # Start monitoring

        # Get upcoming transits for a user
        transits = await service.get_personalized_transits(phone)
    """

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_check_date: Optional[date] = None

    async def start(self):
        """Start the transit monitoring task."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Transit service started")

    async def stop(self):
        """Stop the transit monitoring task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Transit service stopped")

    async def _monitor_loop(self):
        """Main monitoring loop - checks once per day."""
        while self._running:
            try:
                today = date.today()

                # Check once per day
                if self._last_check_date != today:
                    await self._check_transits(today)
                    self._last_check_date = today

                # Sleep for 1 hour before next check
                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Transit monitor error: {e}", exc_info=True)
                await asyncio.sleep(3600)

    async def _check_transits(self, check_date: date):
        """Check for transit events on the given date."""
        logger.info(f"Checking transits for {check_date}")

        # Find events happening today or in next 3 days
        upcoming_window = check_date + timedelta(days=3)

        events_to_notify = []

        for event in UPCOMING_TRANSITS:
            if event.event_date and check_date <= event.event_date <= upcoming_window:
                events_to_notify.append(event)

        # Check retrograde starts/ends
        for planet, periods in RETROGRADE_PERIODS.items():
            for start_date, end_date in periods:
                if check_date <= start_date <= upcoming_window:
                    events_to_notify.append(TransitEvent(
                        event_type=TransitEventType.RETROGRADE_START,
                        planet=planet,
                        event_date=start_date,
                        description=f"{planet.title()} goes retrograde",
                        impact_level="medium"
                    ))
                if check_date <= end_date <= upcoming_window:
                    events_to_notify.append(TransitEvent(
                        event_type=TransitEventType.RETROGRADE_END,
                        planet=planet,
                        event_date=end_date,
                        description=f"{planet.title()} goes direct",
                        impact_level="medium"
                    ))

        if events_to_notify:
            await self._send_transit_alerts(events_to_notify)

    async def _send_transit_alerts(self, events: List[TransitEvent]):
        """Send transit alerts to subscribed users."""
        service = get_subscription_service()

        # Get all transit alert subscribers
        # Note: In production, this would be a proper DB query
        subscribers = await service.get_due_subscribers(
            SubscriptionType.TRANSIT_ALERTS,
            target_time=datetime.now().strftime("%H:%M")
        )

        if not subscribers:
            # Fallback: get all transit subscribers regardless of time
            # This is a simplified approach
            return

        for subscription in subscribers:
            try:
                await self._send_personalized_alert(subscription, events)
            except Exception as e:
                logger.error(f"Error sending transit alert to {subscription.phone}: {e}")

    async def _send_personalized_alert(
        self,
        subscription: Subscription,
        events: List[TransitEvent]
    ):
        """Send personalized transit alert to a user."""
        phone = subscription.phone

        # Get user's birth chart for personalization
        from common.stores import get_store
        store = get_store()
        user = await store.get_user(phone)

        # Filter events based on user's preferences
        alert_planets = subscription.alert_planets or ["saturn", "jupiter", "rahu", "ketu"]
        relevant_events = [
            e for e in events
            if e.planet.lower() in alert_planets
        ]

        if not relevant_events:
            return

        # Format and send message
        message = self._format_transit_alert(relevant_events, user)
        await self._send_whatsapp_message(phone, message)

        logger.info(f"Sent transit alert to {phone}")

    def _format_transit_alert(self, events: List[TransitEvent], user=None) -> str:
        """Format transit events into a WhatsApp message."""
        lines = [
            "🪐 *Planetary Transit Alert*",
            "",
        ]

        for event in events:
            emoji = self._get_planet_emoji(event.planet)
            date_str = event.event_date.strftime("%d %b") if event.event_date else "Soon"

            lines.append(f"{emoji} *{event.planet.title()}* - {date_str}")
            lines.append(f"   {event.description}")

            # Add personalized impact if user has birth chart
            if user and user.moon_sign:
                impact = self._calculate_personal_impact(event, user)
                if impact:
                    lines.append(f"   _Impact on you: {impact}_")

            lines.append("")

        # Add advice
        lines.append("*General Advice:*")
        lines.append("- Avoid major decisions during retrogrades")
        lines.append("- Sign changes bring new energy - adapt gradually")
        lines.append("")
        lines.append("_Reply 'stop alerts' to unsubscribe_")

        return "\n".join(lines)

    def _get_planet_emoji(self, planet: str) -> str:
        """Get emoji for planet."""
        emojis = {
            "sun": "☀️",
            "moon": "🌙",
            "mercury": "☿️",
            "venus": "♀️",
            "mars": "♂️",
            "jupiter": "♃",
            "saturn": "♄",
            "rahu": "☊",
            "ketu": "☋",
        }
        return emojis.get(planet.lower(), "🪐")

    def _calculate_personal_impact(self, event: TransitEvent, user) -> Optional[str]:
        """Calculate personalized impact based on user's chart."""
        if not user or not user.moon_sign:
            return None

        moon_sign = user.moon_sign.lower()
        to_sign = (event.to_sign or "").lower()

        if not to_sign:
            return None

        # Calculate house from moon sign
        try:
            moon_idx = SIGNS.index(moon_sign)
            transit_idx = SIGNS.index(to_sign)
            house = ((transit_idx - moon_idx) % 12) + 1
        except ValueError:
            return None

        # House impact descriptions
        house_impacts = {
            1: "Self, personality, new beginnings",
            2: "Finances, family, speech",
            3: "Siblings, communication, short travel",
            4: "Home, mother, emotional peace",
            5: "Children, creativity, romance",
            6: "Health, enemies, daily work",
            7: "Marriage, partnerships, business",
            8: "Transformation, inheritance, secrets",
            9: "Fortune, father, long travel",
            10: "Career, status, public image",
            11: "Gains, friends, aspirations",
            12: "Expenses, spirituality, foreign lands",
        }

        return f"Transits your {house}th house - {house_impacts.get(house, 'General influence')}"

    async def _send_whatsapp_message(self, phone: str, message: str):
        """Send message via WhatsApp."""
        from common.whatsapp.client import send_text_message
        try:
            await send_text_message(phone, message)
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            raise

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def get_upcoming_transits(self, days: int = 30) -> List[TransitEvent]:
        """
        Get upcoming transit events.

        Args:
            days: Number of days to look ahead

        Returns:
            List of upcoming transit events
        """
        today = date.today()
        end_date = today + timedelta(days=days)

        upcoming = []

        for event in UPCOMING_TRANSITS:
            if event.event_date and today <= event.event_date <= end_date:
                upcoming.append(event)

        # Add retrograde events
        for planet, periods in RETROGRADE_PERIODS.items():
            for start_date, end_date_period in periods:
                if today <= start_date <= end_date:
                    upcoming.append(TransitEvent(
                        event_type=TransitEventType.RETROGRADE_START,
                        planet=planet,
                        event_date=start_date,
                        description=f"{planet.title()} retrograde begins"
                    ))
                if today <= end_date_period <= end_date:
                    upcoming.append(TransitEvent(
                        event_type=TransitEventType.RETROGRADE_END,
                        planet=planet,
                        event_date=end_date_period,
                        description=f"{planet.title()} goes direct"
                    ))

        # Sort by date
        upcoming.sort(key=lambda e: e.event_date or date.max)

        return upcoming

    async def get_personalized_transits(self, phone: str) -> Dict[str, Any]:
        """
        Get personalized transit information for a user.

        Args:
            phone: User's phone number

        Returns:
            Dict with transit information and personal impacts
        """
        from common.stores import get_store
        store = get_store()
        user = await store.get_user(phone)

        upcoming = await self.get_upcoming_transits(30)

        result = {
            "upcoming_transits": [],
            "current_retrogrades": [],
            "personal_impacts": []
        }

        today = date.today()

        # Check current retrogrades
        for planet, periods in RETROGRADE_PERIODS.items():
            for start_date, end_date in periods:
                if start_date <= today <= end_date:
                    result["current_retrogrades"].append({
                        "planet": planet,
                        "until": end_date.strftime("%d %b %Y")
                    })

        # Add upcoming transits with personal impact
        for event in upcoming[:5]:  # Limit to 5
            transit_info = {
                "planet": event.planet,
                "event": event.event_type.value,
                "date": event.event_date.strftime("%d %b %Y") if event.event_date else None,
                "description": event.description
            }

            if user and user.moon_sign:
                impact = self._calculate_personal_impact(event, user)
                if impact:
                    transit_info["personal_impact"] = impact

            result["upcoming_transits"].append(transit_info)

        return result

    def is_planet_retrograde(self, planet: str) -> bool:
        """Check if a planet is currently retrograde."""
        today = date.today()
        periods = RETROGRADE_PERIODS.get(planet.lower(), [])

        for start_date, end_date in periods:
            if start_date <= today <= end_date:
                return True
        return False


# =============================================================================
# SINGLETON
# =============================================================================

_transit_service: Optional[TransitService] = None


def get_transit_service() -> TransitService:
    """Get singleton TransitService instance."""
    global _transit_service
    if _transit_service is None:
        _transit_service = TransitService()
    return _transit_service


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def start_transit_service():
    """Start the transit monitoring service."""
    service = get_transit_service()
    await service.start()


async def stop_transit_service():
    """Stop the transit monitoring service."""
    service = get_transit_service()
    await service.stop()
