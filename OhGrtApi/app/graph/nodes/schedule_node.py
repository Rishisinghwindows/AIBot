"""
Schedule Node - Handles scheduling tasks via chat interface.

Parses natural language schedule requests and creates scheduled tasks.
"""
from app.graph.state import BotState
from app.services.schedule_parser import parse_schedule, extract_task_from_message
from app.logger import logger

INTENT = "set_reminder"


async def handle_schedule(state: BotState) -> dict:
    """
    Handle schedule/reminder intent.

    Creates a scheduled task from natural language.

    Args:
        state: Current bot state with message and session info

    Returns:
        Updated state with response text
    """
    message = state.get("current_query", "")
    session_id = state["whatsapp_message"].get("from_number", "")
    user_id = state.get("user_id")

    if not message:
        return {
            "response_text": (
                "*Schedule a Task*\n\n"
                "Tell me what you'd like to schedule.\n\n"
                "*Examples:*\n"
                "- Remind me to check portfolio at 12 pm daily\n"
                "- Schedule alert every Monday at 9 am\n"
                "- Set reminder for tomorrow at 3 pm"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": None,
        }

    # Parse the schedule from natural language
    parsed = parse_schedule(message)
    title, agent_prompt = extract_task_from_message(message)

    # Try to create the task via database
    try:
        from app.db.base import SessionLocal
        from app.tasks.service import ScheduledTaskService
        from uuid import UUID

        db = SessionLocal()
        try:
            service = ScheduledTaskService(db)

            # Determine ownership
            task_user_id = None
            task_session_id = None

            if user_id:
                try:
                    task_user_id = UUID(user_id)
                except ValueError:
                    pass

            if not task_user_id and session_id:
                task_session_id = session_id

            if not task_user_id and not task_session_id:
                return {
                    "response_text": (
                        "*Scheduling Error*\n\n"
                        "I couldn't identify your session to save the task.\n"
                        "Please try again."
                    ),
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                    "error": "No session or user ID",
                }

            # Create the task
            task = service.create_task(
                title=title,
                description=f"Created via chat: {message}",
                task_type="scheduled_query" if agent_prompt else "reminder",
                schedule_type=parsed.schedule_type,
                user_id=task_user_id,
                session_id=task_session_id,
                scheduled_at=parsed.scheduled_at,
                cron_expression=parsed.cron_expression,
                task_timezone="Asia/Kolkata",  # Default to IST for Indian users
                agent_prompt=agent_prompt,
                notify_via={"push": True},
            )

            # Format response
            response = f"✅ *Scheduled Task Created*\n\n"
            response += f"*Title:* {task.title}\n"
            response += f"*Schedule:* {parsed.description}\n"
            if task.next_run_at:
                next_run_str = task.next_run_at.strftime("%d %b %Y at %I:%M %p")
                response += f"*Next Run:* {next_run_str}\n"

            if parsed.schedule_type == "cron":
                response += f"\n_This will repeat {parsed.description.lower()}._"
            elif parsed.schedule_type == "one_time":
                response += "\n_This is a one-time reminder._"

            response += "\n\nYou can view and manage your scheduled tasks in the Tasks section."

            logger.info(
                "schedule_created_via_chat",
                task_id=str(task.id),
                title=title,
                schedule_type=parsed.schedule_type,
                session_id=session_id[:8] if session_id else None,
            )

            return {
                "tool_result": {
                    "success": True,
                    "data": {
                        "task_id": str(task.id),
                        "title": task.title,
                        "schedule_type": parsed.schedule_type,
                        "description": parsed.description,
                    },
                    "tool_name": "schedule_task",
                },
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
                "error": None,
            }

        finally:
            db.close()

    except Exception as e:
        logger.error("schedule_creation_error", error=str(e), message=message)
        return {
            "response_text": (
                f"*Scheduling*\n\n"
                f"I understood you want to schedule: *{title}*\n"
                f"Schedule: {parsed.description}\n\n"
                f"However, I couldn't save it right now. Please try again later."
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
        }
