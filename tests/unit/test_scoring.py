from datetime import UTC, datetime, timedelta

from app.ingestion.expiry import expiry_status
from app.ingestion.scoring import classify_fit, fingerprint, score_item


def test_explicit_bpharm_is_strong_fit():
    assert classify_fit("Clinical internship", "B.Pharm or Bachelor of Pharmacy") == "strong_fit"


def test_unrelated_mandatory_degree_is_rejected():
    assert classify_fit("Medical role", "MBBS only") == "not_fit"


def test_official_bpharm_item_scores_highly():
    result = score_item(
        title="B.Pharm internship",
        eligibility="B.Pharm accepted",
        summary="Apply for this entry-level pharmacy internship with training and mentorship.",
        location="India",
        trust_level="official_verified",
        deadline=datetime.now(UTC) + timedelta(days=10),
    )
    assert result.fit == "strong_fit"
    assert result.score >= 80


def test_expiry_bands():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert expiry_status(now - timedelta(seconds=1), now) == "EXPIRED"
    assert expiry_status(now + timedelta(days=2), now) == "EXPIRING_SOON"
    assert expiry_status(now + timedelta(days=10), now) == "ACTIVE"


def test_fingerprint_is_stable():
    args = ("Acme", "QA internship", "India", None)
    assert fingerprint(*args) == fingerprint(*args)
