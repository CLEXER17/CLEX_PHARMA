from sqlalchemy import select

from app.bot.api import TelegramClient
from app.bot.formatting import opportunity_message
from app.db.models import Opportunity, User
from app.db.session import SessionLocal
from app.settings import Settings

COMMANDS = {
    "start",
    "help",
    "status",
    "latest",
    "internships",
    "jobs",
    "govt",
    "exams",
    "notices",
    "deadlines",
    "search",
    "sources",
    "settings",
    "pause",
    "resume",
}


async def handle_update(update: dict, settings: Settings, telegram: TelegramClient) -> None:
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    user_info = message.get("from") or {}
    telegram_id = user_info.get("id")
    text = (message.get("text") or "").strip()
    if not chat_id or not telegram_id:
        return
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.telegram_id == telegram_id))
        if not user:
            user = User(telegram_id=telegram_id, chat_id=chat_id)
            db.add(user)
            db.commit()
        if not text.startswith("/"):
            return
        command, _, argument = text[1:].partition(" ")
        command = command.split("@", 1)[0].lower()
        if command not in COMMANDS:
            return
        if command in {"start", "help"}:
            response = (
                "CLEX Pharma finds verified India-wide B.Pharm opportunities. "
                "Use /latest, /internships, /jobs, /govt, /exams, "
                "/search &lt;terms&gt;, /pause, or /resume."
            )
        elif command == "pause":
            user.paused = True
            db.commit()
            response = "Alerts paused. Use /resume to enable them again."
        elif command == "resume":
            user.paused = False
            db.commit()
            response = "Alerts resumed."
        elif command == "status":
            active = db.scalar(
                select(Opportunity)
                .where(Opportunity.expiry_status != "EXPIRED")
                .order_by(Opportunity.score.desc())
                .limit(1)
            )
            highest = active.score if active else "No indexed opportunities"
            response = f"Bot online. Highest current score: {highest}"
        else:
            query = (
                select(Opportunity)
                .where(Opportunity.expiry_status != "EXPIRED")
                .order_by(Opportunity.score.desc())
                .limit(5)
            )
            if command == "internships":
                query = query.where(Opportunity.category.ilike("%intern%"))
            elif command == "jobs":
                query = query.where(Opportunity.category.ilike("%job%"))
            elif command in {"govt", "exams", "notices"}:
                query = query.where(
                    Opportunity.category.ilike(
                        f"%{command[:-1] if command == 'exams' else command}%"
                    )
                )
            elif command == "search" and argument:
                query = query.where(Opportunity.title.ilike(f"%{argument}%"))
            rows = list(db.scalars(query))
            response = (
                "\n\n".join(opportunity_message(row) for row in rows)
                if rows
                else "No matching verified opportunities found yet."
            )
        await telegram.send_message(chat_id, response)
