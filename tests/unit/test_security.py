import pytest

from app.ingestion.security import UnsafeURL, looks_blocked, validate_external_url


def test_block_page_detection():
    assert looks_blocked("Please complete the CAPTCHA to continue")
    assert looks_blocked("unavailable", 403)


def test_localhost_is_rejected():
    with pytest.raises(UnsafeURL):
        validate_external_url("http://localhost:8000/health")
