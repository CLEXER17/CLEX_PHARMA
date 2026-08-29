import pytest

from app.ingestion.adapters.rss import RSSAdapter


@pytest.mark.asyncio
async def test_rss_adapter_categorizes_internship_entries(monkeypatch):
    monkeypatch.setattr("app.ingestion.adapters.rss.validate_external_url", lambda url: url)
    body = """
    <rss version="2.0"><channel><item>
      <title>Pharmacy trainee internship</title>
      <link>/opportunities/1</link>
      <description>Training opportunity for pharmacy graduates.</description>
    </item></channel></rss>
    """
    adapter = RSSAdapter(lambda _url: _body(body))
    items = await adapter.discover("https://example.gov.in/feed.xml")
    assert len(items) == 1
    assert items[0].category == "internship"


async def _body(value: str) -> str:
    return value
