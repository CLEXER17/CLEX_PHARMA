import pytest

from app.ingestion.adapters.html import HTMLAdapter


@pytest.mark.asyncio
async def test_html_adapter_discovers_relevant_same_host_links(monkeypatch):
    monkeypatch.setattr("app.ingestion.adapters.html.validate_external_url", lambda url: url)
    html = """
    <html><head><title>Recruitment</title></head><body>
      <a href="/pharmacist-vacancy">Pharmacist vacancy</a>
      <a href="https://other.example/jobs">B.Pharm job</a>
      <a href="/about">About us</a>
      <a href="/pharmacist-vacancy#latest">Pharmacist vacancy duplicate</a>
    </body></html>
    """
    adapter = HTMLAdapter(lambda _url: _body(html))
    items = await adapter.discover(
        "https://example.gov.in/", organization="Example", source_trust="official_verified"
    )
    assert len(items) == 1
    assert items[0].url == "https://example.gov.in/pharmacist-vacancy"
    assert items[0].category == "government job"
    assert items[0].source_trust == "official_verified"


@pytest.mark.asyncio
async def test_html_adapter_matches_relevant_path_when_anchor_is_generic(monkeypatch):
    monkeypatch.setattr("app.ingestion.adapters.html.validate_external_url", lambda url: url)
    html = '<a href="/notifications/recruitment/2026">View details</a>'
    adapter = HTMLAdapter(lambda _url: _body(html), terms=("recruitment",))
    items = await adapter.discover("https://example.gov.in/")
    assert [item.url for item in items] == [
        "https://example.gov.in/notifications/recruitment/2026"
    ]

    monkeypatch.setattr("app.ingestion.adapters.html.validate_external_url", lambda url: url)
    adapter = HTMLAdapter(lambda _url: _body('<a href="/about">About the organization</a>'))
    assert await adapter.discover("https://example.gov.in/") == []


async def _body(value: str) -> str:
    return value
