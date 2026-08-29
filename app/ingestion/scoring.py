import re
from dataclasses import dataclass
from datetime import UTC, datetime

FIT_VALUES = {
    "strong_fit": 1.0,
    "possible_fit": 0.7,
    "weak_fit": 0.35,
    "unknown": 0.25,
    "not_fit": 0.0,
}
ROLE_TERMS = (
    "pharmacy",
    "pharmaceutical",
    "pharmacovigilance",
    "drug safety",
    "quality assurance",
    "quality control",
    "regulatory",
    "clinical research",
    "medical writing",
    "formulation",
)
EXPLICIT_TERMS = ("b.pharm", "b pharm", "bachelor of pharmacy", "pharmacy graduate")
NEGATIVE_DEGREES = ("mbbs only", "b.tech only", "engineering only", "ca only")


@dataclass(frozen=True, slots=True)
class ScoreResult:
    fit: str
    score: int
    reasons: tuple[str, ...]


def classify_fit(title: str, eligibility: str, summary: str = "") -> str:
    text = f"{title} {eligibility} {summary}".lower()
    if any(term in text for term in NEGATIVE_DEGREES) and not any(
        term in text for term in EXPLICIT_TERMS
    ):
        return "not_fit"
    if any(term in text for term in EXPLICIT_TERMS):
        return "strong_fit"
    if any(term in text for term in ROLE_TERMS):
        return (
            "possible_fit"
            if "intern" in text or "fresher" in text or "graduate" in text
            else "weak_fit"
        )
    return "unknown"


def score_item(
    *,
    title: str,
    eligibility: str,
    summary: str,
    location: str,
    trust_level: str,
    deadline: datetime | None,
    now: datetime | None = None,
) -> ScoreResult:
    now = now or datetime.now(UTC)
    fit = classify_fit(title, eligibility, summary)
    score = round(FIT_VALUES[fit] * 45)
    reasons = [f"B.Pharm fit: {fit}"]
    trust_points = {
        "official_verified": 20,
        "official_document_verified": 20,
        "cross_checked": 18,
        "source_verified": 14,
        "discovery_only": 5,
        "blocked_or_unverified": 0,
    }.get(trust_level, 0)
    score += trust_points
    reasons.append(f"source trust: +{trust_points}")
    if deadline:
        days = (deadline - now).total_seconds() / 86400
        freshness = 15 if days >= 0 else -20
        if 0 <= days <= 7:
            freshness += 5
        score += freshness
        reasons.append(f"deadline timing: {freshness:+d}")
    else:
        reasons.append("deadline not verified")
    completeness = 10 if len(summary.strip()) >= 30 else 4
    score += completeness
    reasons.append(f"information completeness: +{completeness}")
    location_text = location.lower()
    geography = (
        10
        if "india" in location_text or "nationwide" in location_text
        else 5
        if "remote" in location_text
        else 3
        if location_text.strip() != "not specified / not verified"
        else 0
    )
    score += geography
    reasons.append(f"geography: +{geography}")
    return ScoreResult(fit=fit, score=max(0, min(100, score)), reasons=tuple(reasons))


def fingerprint(organization: str, title: str, location: str, deadline: datetime | None) -> str:
    import hashlib

    normalized = "|".join(
        re.sub(r"\W+", " ", value.lower()).strip()
        for value in (organization, title, location, deadline.isoformat() if deadline else "")
    )
    return hashlib.sha256(normalized.encode()).hexdigest()
