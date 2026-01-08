"""
Subscription Service.

Manages user subscriptions for daily horoscope and transit alerts.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# In-memory storage for lite mode
# In production, this should use the database
_subscriptions: Dict[str, List[Dict]] = {}


async def subscribe_horoscope(phone: str, sign: str) -> Dict:
    """
    Subscribe user to daily horoscope.

    Args:
        phone: User's phone number
        sign: Zodiac sign

    Returns:
        Subscription record
    """
    subscription = {
        "type": "horoscope",
        "sign": sign,
        "phone": phone,
        "created_at": datetime.now().isoformat(),
        "active": True,
    }

    if phone not in _subscriptions:
        _subscriptions[phone] = []

    # Remove existing horoscope subscription
    _subscriptions[phone] = [
        s for s in _subscriptions[phone] if s["type"] != "horoscope"
    ]

    _subscriptions[phone].append(subscription)
    logger.info(f"User {phone} subscribed to horoscope for {sign}")

    return subscription


async def subscribe_transit(phone: str) -> Dict:
    """
    Subscribe user to planetary transit alerts.

    Args:
        phone: User's phone number

    Returns:
        Subscription record
    """
    subscription = {
        "type": "transit",
        "phone": phone,
        "created_at": datetime.now().isoformat(),
        "active": True,
    }

    if phone not in _subscriptions:
        _subscriptions[phone] = []

    # Remove existing transit subscription
    _subscriptions[phone] = [
        s for s in _subscriptions[phone] if s["type"] != "transit"
    ]

    _subscriptions[phone].append(subscription)
    logger.info(f"User {phone} subscribed to transit alerts")

    return subscription


async def unsubscribe(phone: str, sub_type: str) -> bool:
    """
    Unsubscribe user from a subscription type.

    Args:
        phone: User's phone number
        sub_type: Subscription type (horoscope, transit)

    Returns:
        True if unsubscribed successfully
    """
    if phone not in _subscriptions:
        return False

    original_count = len(_subscriptions[phone])
    _subscriptions[phone] = [
        s for s in _subscriptions[phone] if s["type"] != sub_type
    ]

    if len(_subscriptions[phone]) < original_count:
        logger.info(f"User {phone} unsubscribed from {sub_type}")
        return True

    return False


async def get_user_subscriptions(phone: str) -> List[Dict]:
    """
    Get all subscriptions for a user.

    Args:
        phone: User's phone number

    Returns:
        List of subscription records
    """
    subscriptions = _subscriptions.get(phone, [])

    # Format for display
    result = []
    for sub in subscriptions:
        if sub["type"] == "horoscope":
            result.append({
                "type": "horoscope",
                "details": f"{sub.get('sign', 'Unknown').title()} - Daily at 6 AM",
            })
        elif sub["type"] == "transit":
            result.append({
                "type": "transit",
                "details": "Planetary transit alerts",
            })

    return result


async def get_horoscope_subscribers() -> List[Dict]:
    """
    Get all users subscribed to horoscope.

    Returns:
        List of subscription records with phone and sign
    """
    subscribers = []
    for phone, subs in _subscriptions.items():
        for sub in subs:
            if sub["type"] == "horoscope" and sub.get("active"):
                subscribers.append({
                    "phone": phone,
                    "sign": sub.get("sign"),
                })
    return subscribers


async def get_transit_subscribers() -> List[str]:
    """
    Get all users subscribed to transit alerts.

    Returns:
        List of phone numbers
    """
    subscribers = []
    for phone, subs in _subscriptions.items():
        for sub in subs:
            if sub["type"] == "transit" and sub.get("active"):
                subscribers.append(phone)
    return subscribers
