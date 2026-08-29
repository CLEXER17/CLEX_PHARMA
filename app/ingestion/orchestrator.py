from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select

from app.db.models import Opportunity, OpportunitySource, Source, SourceRun, utcnow
from app.db.session import SessionLocal
from app.ingestion.adapters.base import DiscoveredItem
from app.ingestion.adapters.html import HTMLAdapter
from app.ingestion.adapters.rss import RSSAdapter
from app.ingestion.config import load_sources, load_terms
from app.ingestion.expiry import expiry_status
from app.ingestion.http_client import SafeHTTPClient
from app.ingestion.scoring import fingerprint, score_item


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", "", ""))


def _meaningful(value: str | None) -> bool:
    return bool(value and value != "Not specified / Not verified")


def _source_record(db, definition: dict) -> Source:
    url = canonicalize_url(str(definition["url"]))
    source = db.scalar(select(Source).where(Source.url == url))
    if source is None:
        source = Source(
            name=str(definition.get("name", url)),
            url=url,
            source_type=str(definition.get("type", "html")),
            trust_level=str(definition.get("trust_level", "source_verified")),
            official=bool(definition.get("official", False)),
        )
        db.add(source)
        db.commit()
    else:
        source.name = str(definition.get("name", source.name))
        source.source_type = str(definition.get("type", source.source_type))
        source.trust_level = str(definition.get("trust_level", source.trust_level))
        source.official = bool(definition.get("official", source.official))
        db.commit()
    return source


def _persist_item(db, item: DiscoveredItem, source: Source) -> tuple[bool, bool]:
    url = canonicalize_url(item.url)
    score = score_item(
        title=item.title,
        eligibility=item.eligibility,
        summary=item.summary,
        location=item.location,
        trust_level=item.source_trust,
        deadline=item.deadline,
    )
    if score.fit == "not_fit":
        return False, False
    now = utcnow()
    values = {
        "title": item.title[:500],
        "organization": item.organization[:300],
        "category": item.category[:80],
        "location": item.location[:300],
        "eligibility": item.eligibility,
        "stipend_salary": item.stipend_salary[:200],
        "summary": item.summary,
        "published_at": item.published_at,
        "deadline": item.deadline,
        "expiry_status": expiry_status(item.deadline, now),
        "fit": score.fit,
        "trust_level": item.source_trust,
        "score": score.score,
        "score_reasons": "; ".join(score.reasons),
        "last_seen": now,
    }
    opportunity = db.scalar(select(Opportunity).where(Opportunity.canonical_url == url))
    inserted = opportunity is None
    if inserted:
        opportunity = Opportunity(
            canonical_url=url,
            fingerprint=fingerprint(item.organization, item.title, item.location, item.deadline),
            first_seen=now,
            **values,
        )
        db.add(opportunity)
        db.flush()
    else:
        for key, value in values.items():
            if key in {"published_at", "deadline"} and value is None:
                continue
            if isinstance(value, str) and not _meaningful(value):
                continue
            setattr(opportunity, key, value)
    link = db.scalar(
        select(OpportunitySource).where(
            OpportunitySource.opportunity_id == opportunity.id,
            OpportunitySource.source_id == source.id,
        )
    )
    if link is None:
        db.add(
            OpportunitySource(
                opportunity_id=opportunity.id, source_id=source.id, original_url=item.url
            )
        )
    db.commit()
    return inserted, not inserted


async def run_ingestion_cycle(
    *, fetcher=None, definitions: list[dict] | None = None
) -> dict[str, int]:
    client = fetcher or SafeHTTPClient()
    fetch_text = client.get_text if hasattr(client, "get_text") else client
    definitions = definitions if definitions is not None else load_sources()
    terms = load_terms()
    totals = {
        "sources": 0,
        "succeeded": 0,
        "failed": 0,
        "discovered": 0,
        "inserted": 0,
        "updated": 0,
    }
    with SessionLocal() as db:
        for definition in definitions:
            source = _source_record(db, definition)
            run = SourceRun(source_id=source.id, status="running", started_at=utcnow())
            db.add(run)
            db.commit()
            totals["sources"] += 1
            try:
                if source.source_type.lower() in {"rss", "atom"}:
                    items = await RSSAdapter(fetch_text).discover(source.url)
                else:
                    items = await HTMLAdapter(fetch_text, terms).discover(
                        source.url,
                        organization=source.name,
                        source_trust=source.trust_level,
                    )
                inserted = updated = 0
                for item in items:
                    try:
                        was_inserted, was_updated = _persist_item(db, item, source)
                        inserted += was_inserted
                        updated += was_updated
                    except Exception:
                        db.rollback()
                run.status = "success"
                run.discovered = len(items)
                run.completed_at = utcnow()
                source.last_success = run.completed_at
                source.last_error = None
                db.commit()
                totals["succeeded"] += 1
                totals["discovered"] += len(items)
                totals["inserted"] += inserted
                totals["updated"] += updated
            except Exception as exc:
                db.rollback()
                run = db.get(SourceRun, run.id)
                source = db.get(Source, source.id)
                run.status = "failed"
                run.error = f"{type(exc).__name__}: {str(exc)[:1000]}"
                run.completed_at = utcnow()
                source.last_error = run.error
                db.commit()
                totals["failed"] += 1
    return totals
