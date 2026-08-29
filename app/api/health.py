from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import func, select, text

from app.db.models import Opportunity, Source
from app.db.session import SessionLocal

router = APIRouter()
started_at = datetime.now(UTC)


@router.get("/health/live")
def live() -> dict:
    return {"status": "ok", "started_at": started_at.isoformat()}


@router.get("/health/ready")
def ready() -> dict:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        return {"status": "not_ready", "database": "error", "error": type(exc).__name__}


@router.get("/health")
def health() -> dict:
    try:
        with SessionLocal() as db:
            sources = db.scalar(select(func.count(Source.id))) or 0
            blocked = (
                db.scalar(select(func.count(Source.id)).where(Source.last_error.is_not(None))) or 0
            )
            opportunities = db.scalar(select(func.count(Opportunity.id))) or 0
        return {
            "status": "ok",
            "database": "ok",
            "active_sources": sources,
            "blocked_sources": blocked,
            "opportunities": opportunities,
        }
    except Exception as exc:
        return {"status": "degraded", "database": "error", "error": type(exc).__name__}
