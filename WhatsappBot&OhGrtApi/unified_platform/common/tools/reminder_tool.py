"""
Reminder Tool

Tool to set reminders.
"""

import os
from datetime import datetime, timedelta
import parsedatetime as pdt
from common.graph.state import ToolResult


def _parse_datetime(time_str: str) -> datetime:
    """Parses a natural language time string into a datetime object."""
    cal = pdt.Calendar()
    time_struct, parse_status = cal.parse(time_str)
    if not parse_status:
        raise ValueError(f"Could not parse time: {time_str}")

    dt = datetime(*time_struct[:6])
    if dt < datetime.now():
        # If the parsed time is in the past, assume it's for today but later
        # or for tomorrow, depending on how far in the past it is.
        dt += timedelta(days=1)
        if dt < datetime.now():
            dt += timedelta(days=1)
    return dt


def _is_lite_mode() -> bool:
    """Check if running in lite mode (CLI/Chainlit without WhatsApp)."""
    return os.getenv("LITE_MODE", "false").lower() == "true"


async def set_reminder(time_str: str, message: str, to_number: str) -> ToolResult:
    """
    Sets a reminder for the user.

    Args:
        time_str: Natural language string for the reminder time (e.g., "in 5 minutes", "tomorrow at 9 AM").
        message: The reminder message.
        to_number: The WhatsApp number to send the reminder to.

    Returns:
        ToolResult with success/failure status.
    """
    try:
        reminder_time = _parse_datetime(time_str)

        # Check if scheduler is running, or use lite mode
        try:
            from common.services.reminder_service import ReminderService
            reminder_id = ReminderService.add_reminder(reminder_time, to_number, message)

            return ToolResult(
                success=True,
                data={"reminder_id": reminder_id, "scheduled_time": reminder_time.strftime("%Y-%m-%d %H:%M")},
                error=None,
                tool_name="set_reminder",
            )
        except Exception as scheduler_error:
            # Scheduler not running - return success with demo mode
            if "scheduler is not running" in str(scheduler_error).lower() or "cli_test" in to_number or "chainlit" in to_number:
                # Demo/lite mode - just show what would happen
                return ToolResult(
                    success=True,
                    data={
                        "reminder_id": f"demo_{datetime.now().timestamp()}",
                        "scheduled_time": reminder_time.strftime("%Y-%m-%d %H:%M"),
                        "demo_mode": True,
                    },
                    error=None,
                    tool_name="set_reminder",
                )
            raise scheduler_error

    except ValueError as e:
        return ToolResult(
            success=False,
            data=None,
            error=f"Invalid time format. Please try a clear time like 'in 5 minutes' or 'tomorrow at 9 AM'.",
            tool_name="set_reminder",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="set_reminder",
        )

