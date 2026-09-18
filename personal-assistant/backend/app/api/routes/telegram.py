"""Telegram bot integration for the AI Personal Assistant."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.agent.state import AgentState
from app.db.repositories import ConversationRepository, MessageRepository
from app.llm.provider import get_llm_provider
from app.tools.registry import get_tool_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/telegram", tags=["telegram"])


class TelegramMessage(BaseModel):
    """Telegram message update."""

    update_id: int
    message_id: int
    chat_id: int
    user_id: int
    text: str
    username: Optional[str] = None
    first_name: Optional[str] = None


class TelegramWebhookPayload(BaseModel):
    """Telegram webhook payload."""

    update_id: int
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None
    channel_post: Optional[TelegramMessage] = None


async def send_telegram_message(
    bot_token: str, chat_id: int, text: str, reply_to_message_id: Optional[int] = None
) -> bool:
    """Send a message to Telegram."""
    import aiohttp

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                return result.get("ok", False)
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


@router.post("/webhook")
async def telegram_webhook(payload: dict, request: Request):
    """Handle incoming Telegram messages."""
    from app.config import settings

    # Verify webhook token if configured
    telegram_token = settings.TELEGRAM_BOT_TOKEN
    if not telegram_token:
        raise HTTPException(status_code=400, detail="Telegram bot not configured")

    try:
        # Extract message from update
        if "message" not in payload:
            return {"status": "ok"}  # Ignore non-message updates

        message_data = payload["message"]
        chat_id = message_data["chat"]["id"]
        user_id = message_data["from"]["id"]
        message_id = message_data["message_id"]
        text = message_data.get("text", "")
        username = message_data["from"].get("username")
        first_name = message_data["from"].get("first_name")

        if not text:
            return {"status": "ok"}  # Ignore non-text messages

        # Create conversation context
        conversation_repo = ConversationRepository(request.app.state.db_session)
        message_repo = MessageRepository(request.app.state.db_session)

        # Get or create conversation for this chat
        conversation_id = f"telegram_{chat_id}"
        conversation = await conversation_repo.get_or_create(
            conversation_id=conversation_id,
            user_id=str(user_id),
            title=f"Telegram Chat with {username or first_name or 'User'}",
        )

        # Store user message
        await message_repo.create(
            conversation_id=conversation.id,
            role="user",
            content=text,
        )

        # Process with agent
        llm_provider = get_llm_provider()
        tool_registry = get_tool_registry()

        # Simple agent flow for Telegram
        agent_state: AgentState = {
            "user_id": str(user_id),
            "conversation_id": str(conversation.id),
            "messages": [],
            "user_request": text,
            "retrieved_context": [],
            "memories": [],
            "plan": [],
            "current_step": 0,
            "tool_calls": [],
            "tool_results": [],
            "requires_confirmation": False,
            "confirmation_reason": None,
            "final_response": None,
            "errors": [],
        }

        # Get conversation history
        recent_messages = await message_repo.get_recent(
            conversation_id=conversation.id, limit=10
        )
        agent_state["messages"] = [
            {"role": msg.role, "content": msg.content} for msg in recent_messages
        ]

        # Generate response using LLM
        from app.agent.prompts import TELEGRAM_SYSTEM_PROMPT

        messages_for_llm = [
            {"role": "system", "content": TELEGRAM_SYSTEM_PROMPT},
        ] + agent_state["messages"]

        response = await llm_provider.generate(
            messages=messages_for_llm,
            model=settings.LLM_MODEL,
            max_tokens=500,
        )

        assistant_response = response.content

        # Store assistant response
        await message_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_response,
        )

        # Send response to Telegram
        success = await send_telegram_message(
            bot_token=telegram_token,
            chat_id=chat_id,
            text=assistant_response,
            reply_to_message_id=message_id,
        )

        if not success:
            logger.warning("Failed to send response to Telegram")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing Telegram message: {e}", exc_info=True)
        # Try to send error message
        if "chat_id" in locals():
            await send_telegram_message(
                bot_token=telegram_token,
                chat_id=chat_id,
                text="Sorry, I encountered an error processing your request.",
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-webhook")
async def set_telegram_webhook(request: Request):
    """Set up Telegram webhook."""
    from app.config import settings

    telegram_token = settings.TELEGRAM_BOT_TOKEN
    if not telegram_token:
        raise HTTPException(status_code=400, detail="Telegram bot not configured")

    import aiohttp

    # Get the webhook URL from request or use default
    webhook_url = settings.TELEGRAM_WEBHOOK_URL
    if not webhook_url:
        # Try to construct from request
        host = request.headers.get("host", "localhost:8000")
        scheme = request.headers.get("x-forwarded-proto", "http")
        webhook_url = f"{scheme}://{host}/api/v1/telegram/webhook"

    url = f"https://api.telegram.org/bot{telegram_token}/setWebhook"
    payload = {"url": webhook_url}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if result.get("ok"):
                    return {"status": "success", "webhook_url": webhook_url}
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Telegram API error: {result}"
                    )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook-info")
async def get_webhook_info():
    """Get Telegram webhook info."""
    from app.config import settings
    import aiohttp

    telegram_token = settings.TELEGRAM_BOT_TOKEN
    if not telegram_token:
        raise HTTPException(status_code=400, detail="Telegram bot not configured")

    url = f"https://api.telegram.org/bot{telegram_token}/getWebhookInfo"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                result = await response.json()
                return result.get("result", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
