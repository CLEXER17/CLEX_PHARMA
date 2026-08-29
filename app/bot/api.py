import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.settings import Settings

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    async def send_message(
        self, chat_id: int | str, text: str, reply_markup: dict[str, Any] | None = None
    ) -> bool:
        if not self.settings.telegram_bot_token:
            logger.warning("Telegram message skipped: bot token is not configured")
            return False
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(f"{self.base_url}/sendMessage", json=payload)
        except httpx.HTTPError:
            logger.exception("Telegram sendMessage request failed for chat_id=%s", chat_id)
            return False
        if response.is_success:
            return True
        self._log_api_error("sendMessage", response, chat_id=chat_id)
        return False

    def _log_api_error(
        self, method: str, response: httpx.Response, *, chat_id: int | str | None = None
    ) -> None:
        try:
            body = response.json()
            description = body.get("description") if isinstance(body, dict) else None
        except ValueError:
            description = None
        logger.error(
            "Telegram %s failed: status=%s chat_id=%s description=%s",
            method,
            response.status_code,
            chat_id,
            description or response.text[:500],
        )

    async def set_webhook(self) -> bool:
        if not self.settings.telegram_bot_token or not self.settings.public_base_url:
            return False
        payload = {
            "url": f"{self.settings.public_base_url.rstrip('/')}/telegram/webhook",
            "secret_token": self.settings.telegram_webhook_secret,
        }
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(f"{self.base_url}/setWebhook", json=payload)
        except httpx.HTTPError:
            logger.exception("Telegram setWebhook request failed")
            return False
        if response.is_success:
            return True
        self._log_api_error("setWebhook", response)
        return False

    async def answer_update(
        self, update: dict[str, Any], handler: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        await handler(update)
