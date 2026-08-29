from fastapi import APIRouter, Header, HTTPException, Request

from app.bot.api import TelegramClient
from app.bot.handlers import handle_update
from app.settings import get_settings

router = APIRouter()


@router.post("/telegram/webhook")
async def webhook(
    request: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)
) -> dict:
    settings = get_settings()
    if (
        settings.telegram_webhook_secret
        and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret
    ):
        raise HTTPException(status_code=403, detail="invalid webhook secret")
    update = await request.json()
    await handle_update(update, settings, TelegramClient(settings))
    return {"ok": True}
