"""
Natural language schedule parser.

Parses expressions like:
- "every day at 12 pm"
- "tomorrow at 3pm"
- "every monday at 9am"
- "in 2 hours"
- "weekly on friday"
- "daily at 8:30 am"
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from dataclasses import dataclass

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# Default timezone for parsing (IST for Indian users)
DEFAULT_TIMEZONE = ZoneInfo("Asia/Kolkata")


@dataclass
class ParsedSchedule:
    """Parsed schedule information."""
    schedule_type: str  # one_time, daily, weekly, monthly, cron
    scheduled_at: Optional[datetime] = None
    cron_expression: Optional[str] = None
    description: str = ""


def parse_time(time_str: str) -> Tuple[int, int]:
    """Parse time string like '12pm', '3:30 pm', '15:00' into (hour, minute)."""
    time_str = time_str.lower().strip()

    # Match patterns like "12pm", "12 pm", "12:30pm", "12:30 pm"
    pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
    match = re.match(pattern, time_str)

    if not match:
        return (9, 0)  # Default to 9 AM

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    ampm = match.group(3)

    if ampm == 'pm' and hour != 12:
        hour += 12
    elif ampm == 'am' and hour == 12:
        hour = 0

    return (hour, minute)


def parse_schedule(text: str, tz: ZoneInfo = DEFAULT_TIMEZONE) -> ParsedSchedule:
    """
    Parse natural language schedule expression.

    Examples:
    - "every day at 12 pm" -> daily cron
    - "tomorrow at 3pm" -> one_time
    - "in 2 hours" -> one_time
    - "every monday at 9am" -> weekly cron
    - "daily at 8:30 am" -> daily cron

    Args:
        text: Natural language schedule expression
        tz: Timezone for interpreting times (default: Asia/Kolkata)
    """
    text_lower = text.lower().strip()
    # Use local timezone for "now" so times are interpreted correctly
    now = datetime.now(tz)

    # Pattern: "in X hours/minutes"
    in_match = re.search(r'in\s+(\d+)\s*(hour|minute|min|hr)s?', text_lower)
    if in_match:
        amount = int(in_match.group(1))
        unit = in_match.group(2)
        if 'hour' in unit or 'hr' in unit:
            scheduled = now + timedelta(hours=amount)
        else:
            scheduled = now + timedelta(minutes=amount)
        return ParsedSchedule(
            schedule_type="one_time",
            scheduled_at=scheduled,
            description=f"One-time in {amount} {unit}s"
        )

    # Pattern: "tomorrow at X"
    tomorrow_match = re.search(r'tomorrow\s+(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', text_lower)
    if tomorrow_match:
        hour, minute = parse_time(tomorrow_match.group(1))
        tomorrow = now + timedelta(days=1)
        scheduled = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return ParsedSchedule(
            schedule_type="one_time",
            scheduled_at=scheduled,
            description=f"Tomorrow at {hour}:{minute:02d}"
        )

    # Pattern: "every day at X" or "daily at X" or "at X daily/every day"
    daily_match = re.search(r'(?:every\s+day|daily)\s+(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', text_lower)
    if daily_match:
        hour, minute = parse_time(daily_match.group(1))
        cron = f"{minute} {hour} * * *"
        return ParsedSchedule(
            schedule_type="cron",
            cron_expression=cron,
            description=f"Daily at {hour}:{minute:02d}"
        )

    # Pattern: "at X daily" or "at X every day"
    daily_suffix_match = re.search(r'at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+(?:daily|every\s+day)', text_lower)
    if daily_suffix_match:
        hour, minute = parse_time(daily_suffix_match.group(1))
        cron = f"{minute} {hour} * * *"
        return ParsedSchedule(
            schedule_type="cron",
            cron_expression=cron,
            description=f"Daily at {hour}:{minute:02d}"
        )

    # Pattern: "every X at Y" (weekday)
    weekday_match = re.search(
        r'every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
        text_lower
    )
    if weekday_match:
        day_map = {
            'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3,
            'thursday': 4, 'friday': 5, 'saturday': 6
        }
        day_name = weekday_match.group(1)
        day_num = day_map[day_name]
        hour, minute = parse_time(weekday_match.group(2))
        cron = f"{minute} {hour} * * {day_num}"
        return ParsedSchedule(
            schedule_type="cron",
            cron_expression=cron,
            description=f"Every {day_name.title()} at {hour}:{minute:02d}"
        )

    # Pattern: "weekly on X at Y"
    weekly_match = re.search(
        r'weekly\s+(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?',
        text_lower
    )
    if weekly_match:
        day_map = {
            'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3,
            'thursday': 4, 'friday': 5, 'saturday': 6
        }
        day_name = weekly_match.group(1)
        day_num = day_map[day_name]
        if weekly_match.group(2):
            hour, minute = parse_time(weekly_match.group(2))
        else:
            hour, minute = (9, 0)
        cron = f"{minute} {hour} * * {day_num}"
        return ParsedSchedule(
            schedule_type="cron",
            cron_expression=cron,
            description=f"Every {day_name.title()} at {hour}:{minute:02d}"
        )

    # Pattern: simple time "at X" for today/next occurrence
    at_match = re.search(r'(?:^|\s)at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', text_lower)
    if at_match:
        hour, minute = parse_time(at_match.group(1))
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # If time has passed today, schedule for tomorrow
        if scheduled <= now:
            scheduled += timedelta(days=1)
        return ParsedSchedule(
            schedule_type="one_time",
            scheduled_at=scheduled,
            description=f"At {hour}:{minute:02d}"
        )

    # Pattern: "every X hours"
    interval_match = re.search(r'every\s+(\d+)\s*(hour|minute|min|hr)s?', text_lower)
    if interval_match:
        amount = int(interval_match.group(1))
        unit = interval_match.group(2)
        if 'hour' in unit or 'hr' in unit:
            cron = f"0 */{amount} * * *"
            description = f"Every {amount} hours"
        else:
            cron = f"*/{amount} * * * *"
            description = f"Every {amount} minutes"
        return ParsedSchedule(
            schedule_type="cron",
            cron_expression=cron,
            description=description
        )

    # Pattern: "12 pm" standalone (daily at that time)
    standalone_time = re.search(r'^(\d{1,2}(?::\d{2})?\s*(?:am|pm))$', text_lower)
    if standalone_time:
        hour, minute = parse_time(standalone_time.group(1))
        cron = f"{minute} {hour} * * *"
        return ParsedSchedule(
            schedule_type="cron",
            cron_expression=cron,
            description=f"Daily at {hour}:{minute:02d}"
        )

    # Default: try to extract any time and make it daily
    time_pattern = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))', text_lower)
    if time_pattern:
        hour, minute = parse_time(time_pattern.group(1))
        cron = f"{minute} {hour} * * *"
        return ParsedSchedule(
            schedule_type="cron",
            cron_expression=cron,
            description=f"Daily at {hour}:{minute:02d}"
        )

    # Fallback: daily at 9 AM
    return ParsedSchedule(
        schedule_type="daily",
        description="Daily at 9:00 AM"
    )


def extract_task_from_message(message: str) -> Tuple[str, str]:
    """
    Extract the task/action from a scheduling message.

    Returns (task_title, agent_prompt)

    Examples:
    - "remind me to check portfolio at 12 pm" -> ("Check portfolio", "check portfolio")
    - "schedule alert every day at 9am to review stocks" -> ("Review stocks", "review stocks")
    """
    message_lower = message.lower()

    # Remove scheduling keywords to extract the task
    task_text = message

    # Remove common prefixes
    prefixes = [
        r'remind\s+me\s+to\s+',
        r'schedule\s+(?:an?\s+)?(?:alert|reminder|task)\s+(?:to\s+)?',
        r'set\s+(?:an?\s+)?(?:alert|reminder|alarm)\s+(?:to\s+|for\s+)?',
        r'create\s+(?:an?\s+)?(?:alert|reminder|task)\s+(?:to\s+)?',
        r'please\s+',
        r'can\s+you\s+',
        r'i\s+need\s+to\s+',
        r'i\s+want\s+to\s+',
    ]

    for prefix in prefixes:
        task_text = re.sub(prefix, '', task_text, flags=re.IGNORECASE)

    # Remove scheduling parts (at X, every X, etc.)
    schedule_patterns = [
        r'\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?',
        r'\s+every\s+(?:day|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'\s+daily',
        r'\s+weekly',
        r'\s+monthly',
        r'\s+in\s+\d+\s*(?:hour|minute|min|hr)s?',
        r'\s+tomorrow',
    ]

    for pattern in schedule_patterns:
        task_text = re.sub(pattern, '', task_text, flags=re.IGNORECASE)

    # Clean up and format
    task_text = task_text.strip()
    task_text = re.sub(r'\s+', ' ', task_text)

    if not task_text:
        task_text = "Scheduled reminder"

    # Create title (capitalize first letter)
    title = task_text[0].upper() + task_text[1:] if task_text else "Scheduled reminder"

    return title, task_text
