from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    chat_id: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(1000), unique=True)
    source_type: Mapped[str] = mapped_column(String(30), default="html")
    trust_level: Mapped[str] = mapped_column(String(30), default="source_verified")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    official: Mapped[bool] = mapped_column(Boolean, default=False)
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class Opportunity(Base):
    __tablename__ = "opportunities"
    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(500))
    organization: Mapped[str] = mapped_column(String(300), default="Not specified / Not verified")
    category: Mapped[str] = mapped_column(String(80), default="notice")
    location: Mapped[str] = mapped_column(String(300), default="Not specified / Not verified")
    eligibility: Mapped[str] = mapped_column(Text, default="Not specified / Not verified")
    stipend_salary: Mapped[str] = mapped_column(String(200), default="Not specified / Not verified")
    summary: Mapped[str] = mapped_column(Text, default="Not specified / Not verified")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expiry_status: Mapped[str] = mapped_column(String(20), default="UNKNOWN", index=True)
    fit: Mapped[str] = mapped_column(String(20), default="unknown")
    trust_level: Mapped[str] = mapped_column(String(30), default="discovery_only")
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    score_reasons: Mapped[str] = mapped_column(Text, default="")
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sources: Mapped[list["OpportunitySource"]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )


class OpportunitySource(Base):
    __tablename__ = "opportunity_sources"
    __table_args__ = (UniqueConstraint("opportunity_id", "source_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    original_url: Mapped[str] = mapped_column(String(1000))
    opportunity: Mapped[Opportunity] = relationship(back_populates="sources")


class SourceRun(Base):
    __tablename__ = "source_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    status: Mapped[str] = mapped_column(String(30))
    discovered: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Delivery(Base):
    __tablename__ = "deliveries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"))
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
