from html import escape

from app.db.models import Opportunity


def safe(value: str | None) -> str:
    return escape(value or "Not specified / Not verified")


def opportunity_message(item: Opportunity) -> str:
    deadline = item.deadline.isoformat() if item.deadline else "Not specified / Not verified"
    return "\n".join(
        [
            "━━━━━━━━━━━━━━━━━━",
            "🎓 <b>B.PHARM OPPORTUNITY</b>",
            "━━━━━━━━━━━━━━━━━━",
            f"📌 <b>Title:</b> {safe(item.title)}",
            f"🏢 <b>Organization:</b> {safe(item.organization)}",
            f"📍 <b>Location:</b> {safe(item.location)}",
            f"💼 <b>Type:</b> {safe(item.category)}",
            f"🎓 <b>Eligibility:</b> {safe(item.eligibility)}",
            f"💰 <b>Stipend/Salary:</b> {safe(item.stipend_salary)}",
            f"📅 <b>Deadline:</b> {safe(deadline)}",
            f"⭐ <b>Relevance Score:</b> {item.score}/100",
            f"📝 <b>Summary:</b> {safe(item.summary)}",
            f"🔎 <b>Verification:</b> {safe(item.trust_level)}",
            f"<i>Reasons: {safe(item.score_reasons)}</i>",
            "━━━━━━━━━━━━━━━━━━",
        ]
    )
