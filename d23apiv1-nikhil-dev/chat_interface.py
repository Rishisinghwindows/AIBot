"""
Chainlit Test Interface

Run this with `chainlit run chat_interface.py -w`
"""

import chainlit as cl
from bot.graph import process_message
import uuid

@cl.on_chat_start
async def start():
    cl.user_session.set("session_id", str(uuid.uuid4()))
    await cl.Message(content="Bot is ready!").send()

@cl.on_message
async def main(message: cl.Message):
    session_id = cl.user_session.get("session_id")

    # Create a mock whatsapp_message dictionary
    whatsapp_message = {
        "message_id": str(uuid.uuid4()),
        "from_number": "chainlit_user",
        "phone_number_id": "chainlit_server",
        "timestamp": "now",
        "message_type": "text",
        "text": message.content,
        "media_id": None,
    }

    # Process the message using the asynchronous function
    result = await process_message(whatsapp_message)

    # Send the response back to the user
    response_text = result.get("response_text")
    response_media_url = result.get("response_media_url")
    tool_used = (result.get("tool_result") or {}).get("tool_name")

    if tool_used:
        response_text = f"Tool Used: *{tool_used}*\n\n{response_text}"

    if response_media_url:
        await cl.Message(
            content=response_text or "",
            elements=[cl.Image(url=response_media_url, name="bot-image", display="inline")]
        ).send()
    elif response_text:
        await cl.Message(
            content=response_text
        ).send()
    else:
        await cl.Message(
            content="Sorry, I could not process your request."
        ).send()
