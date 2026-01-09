"""
Subscription Service

Manages user subscriptions for:
- Daily horoscope notifications
- Transit alerts
- Weekly/monthly predictions

Features:
- Subscribe/unsubscribe management
- Preference storage
- Scheduled notification triggers
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, time
from dataclasses import dataclass, asdict, field
from enum import Enum

logger = logging.getLogger(__name__)


class SubscriptionType(Enum):
    """Types of subscriptions available."""
    DAILY_HOROSCOPE = "daily_horoscope"
    TRANSIT_ALERTS = "transit_alerts"
    WEEKLY_PREDICTION = "weekly_prediction"
    MONTHLY_PREDICTION = "monthly_prediction"
    PANCHANG = "daily_panchang"
    FESTIVAL_ALERTS = "festival_alerts"


@dataclass
class Subscription:
    """User subscription data."""
    phone: str
    subscription_type: SubscriptionType
    enabled: bool = True

    # Notification preferences
    preferred_time: str = "07:00"  # HH:MM format
    timezone: str = "Asia/Kolkata"

    # For horoscope subscriptions
    zodiac_sign: Optional[str] = None
    moon_sign: Optional[str] = None

    # For transit alerts
    alert_planets: List[str] = field(default_factory=lambda: ["saturn", "jupiter", "rahu", "ketu"])
    alert_on_house_transit: bool = True
    alert_on_retrograde: bool = True

    # Metadata
    created_at: Optional[datetime] = None
    last_sent: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["subscription_type"] = self.subscription_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Subscription":
        """Create from dictionary."""
        data = data.copy()
        data["subscription_type"] = SubscriptionType(data["subscription_type"])
        return cls(**data)


class SubscriptionService:
    """
    Manages user subscriptions.

    Usage:
        service = get_subscription_service()
        await service.subscribe(phone, SubscriptionType.DAILY_HOROSCOPE, zodiac_sign="aries")
        await service.unsubscribe(phone, SubscriptionType.DAILY_HOROSCOPE)

        # Get all subscribers for daily horoscope at 7 AM
        subscribers = await service.get_due_subscribers(
            SubscriptionType.DAILY_HOROSCOPE,
            target_time="07:00"
        )
    """

    def __init__(self):
        self._subscriptions: Dict[str, Dict[str, Subscription]] = {}  # phone -> type -> subscription
        self._initialized = False

    async def _get_store(self):
        """Get the appropriate store based on mode."""
        from common.stores import get_store
        return get_store()

    async def subscribe(
        self,
        phone: str,
        subscription_type: SubscriptionType,
        preferred_time: str = "07:00",
        zodiac_sign: str = None,
        moon_sign: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Subscribe user to a notification type.

        Args:
            phone: User's phone number
            subscription_type: Type of subscription
            preferred_time: Preferred notification time (HH:MM)
            zodiac_sign: User's zodiac sign (for horoscope)
            moon_sign: User's moon sign (for Vedic predictions)
            **kwargs: Additional subscription options

        Returns:
            Result with subscription details
        """
        try:
            # Get user profile for birth details
            store = await self._get_store()
            user = await store.get_user(phone)

            # Auto-fill zodiac/moon sign from profile if available
            if user:
                if not zodiac_sign and user.sun_sign:
                    zodiac_sign = user.sun_sign
                if not moon_sign and user.moon_sign:
                    moon_sign = user.moon_sign

            # For horoscope subscriptions, we need at least a zodiac sign
            if subscription_type == SubscriptionType.DAILY_HOROSCOPE and not zodiac_sign:
                return {
                    "success": False,
                    "error": "missing_zodiac",
                    "message": "Please provide your zodiac sign to subscribe to daily horoscope."
                }

            # Create subscription
            subscription = Subscription(
                phone=phone,
                subscription_type=subscription_type,
                preferred_time=preferred_time,
                zodiac_sign=zodiac_sign,
                moon_sign=moon_sign,
                created_at=datetime.now(),
                **kwargs
            )

            # Store in memory
            if phone not in self._subscriptions:
                self._subscriptions[phone] = {}
            self._subscriptions[phone][subscription_type.value] = subscription

            # Persist to database
            await self._save_subscription(phone, subscription)

            logger.info(f"User {phone} subscribed to {subscription_type.value}")

            return {
                "success": True,
                "subscription": subscription.to_dict(),
                "message": f"Successfully subscribed to {subscription_type.value}!"
            }

        except Exception as e:
            logger.error(f"Error subscribing {phone} to {subscription_type}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create subscription. Please try again."
            }

    async def unsubscribe(
        self,
        phone: str,
        subscription_type: SubscriptionType
    ) -> Dict[str, Any]:
        """
        Unsubscribe user from a notification type.

        Args:
            phone: User's phone number
            subscription_type: Type to unsubscribe from

        Returns:
            Result dict
        """
        try:
            # Remove from memory
            if phone in self._subscriptions:
                if subscription_type.value in self._subscriptions[phone]:
                    del self._subscriptions[phone][subscription_type.value]

            # Remove from database
            await self._delete_subscription(phone, subscription_type)

            logger.info(f"User {phone} unsubscribed from {subscription_type.value}")

            return {
                "success": True,
                "message": f"Successfully unsubscribed from {subscription_type.value}."
            }

        except Exception as e:
            logger.error(f"Error unsubscribing {phone} from {subscription_type}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_user_subscriptions(self, phone: str) -> List[Subscription]:
        """
        Get all subscriptions for a user.

        Args:
            phone: User's phone number

        Returns:
            List of active subscriptions
        """
        # Check memory cache first
        if phone in self._subscriptions:
            return list(self._subscriptions[phone].values())

        # Load from database
        subscriptions = await self._load_user_subscriptions(phone)

        # Cache in memory
        if subscriptions:
            self._subscriptions[phone] = {
                s.subscription_type.value: s for s in subscriptions
            }

        return subscriptions

    async def is_subscribed(
        self,
        phone: str,
        subscription_type: SubscriptionType
    ) -> bool:
        """Check if user is subscribed to a type."""
        subs = await self.get_user_subscriptions(phone)
        return any(s.subscription_type == subscription_type and s.enabled for s in subs)

    async def get_due_subscribers(
        self,
        subscription_type: SubscriptionType,
        target_time: str = None
    ) -> List[Subscription]:
        """
        Get subscribers who should receive notification now.

        Args:
            subscription_type: Type of subscription
            target_time: Time to match (HH:MM), or current time if None

        Returns:
            List of subscriptions due for notification
        """
        if target_time is None:
            target_time = datetime.now().strftime("%H:%M")

        # Load all subscriptions of this type
        all_subs = await self._load_all_subscriptions(subscription_type)

        # Filter by time (with 5-minute window)
        due_subs = []
        target_minutes = self._time_to_minutes(target_time)

        for sub in all_subs:
            if not sub.enabled:
                continue

            sub_minutes = self._time_to_minutes(sub.preferred_time)

            # 5-minute window
            if abs(sub_minutes - target_minutes) <= 5:
                due_subs.append(sub)

        return due_subs

    async def update_last_sent(self, phone: str, subscription_type: SubscriptionType):
        """Update the last_sent timestamp for a subscription."""
        if phone in self._subscriptions:
            if subscription_type.value in self._subscriptions[phone]:
                self._subscriptions[phone][subscription_type.value].last_sent = datetime.now()

        await self._update_last_sent_db(phone, subscription_type)

    # =========================================================================
    # PERSISTENCE METHODS (to be implemented with actual DB)
    # =========================================================================

    async def _save_subscription(self, phone: str, subscription: Subscription):
        """Save subscription to database."""
        try:
            store = await self._get_store()
            await store.save_context(
                phone=phone,
                context_type=f"subscription:{subscription.subscription_type.value}",
                context_data=subscription.to_dict(),
                expires_in_minutes=60 * 24 * 365  # 1 year
            )
        except Exception as e:
            logger.error(f"Error saving subscription: {e}")

    async def _delete_subscription(self, phone: str, subscription_type: SubscriptionType):
        """Delete subscription from database."""
        try:
            store = await self._get_store()
            await store.clear_context(phone, f"subscription:{subscription_type.value}")
        except Exception as e:
            logger.error(f"Error deleting subscription: {e}")

    async def _load_user_subscriptions(self, phone: str) -> List[Subscription]:
        """Load all subscriptions for a user from database."""
        subscriptions = []
        store = await self._get_store()

        for sub_type in SubscriptionType:
            try:
                data = await store.get_context(phone, f"subscription:{sub_type.value}")
                if data:
                    subscriptions.append(Subscription.from_dict(data))
            except Exception as e:
                logger.error(f"Error loading subscription {sub_type}: {e}")

        return subscriptions

    async def _load_all_subscriptions(self, subscription_type: SubscriptionType) -> List[Subscription]:
        """
        Load all subscriptions of a type from database.

        Note: In production, this should be a proper DB query.
        For now, returns cached subscriptions.
        """
        all_subs = []
        for phone, subs in self._subscriptions.items():
            if subscription_type.value in subs:
                all_subs.append(subs[subscription_type.value])
        return all_subs

    async def _update_last_sent_db(self, phone: str, subscription_type: SubscriptionType):
        """Update last_sent in database."""
        # Will be implemented with proper DB
        pass

    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight."""
        try:
            parts = time_str.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return 7 * 60  # Default to 7 AM


# =============================================================================
# SINGLETON
# =============================================================================

_subscription_service: Optional[SubscriptionService] = None


def get_subscription_service() -> SubscriptionService:
    """Get singleton SubscriptionService instance."""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service
