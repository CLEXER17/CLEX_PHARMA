from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

import feedparser

from app.ingestion.adapters.base import DiscoveredItem
from app.ingestion.security import validate_external_url


class RSSAdapter:
    def __init__(self, fetcher):
        self.fetcher = fetcher

    async def discover(self, source_url: str) -> list[DiscoveredItem]:
        url = validate_external_url(source_url)
        body = await self.fetcher(url)
        feed = feedparser.parse(body)
        result = []
        for entry in feed.entries:
            link = urljoin(url, entry.get("link", ""))
            if not link:
                continue
            published = None
            if entry.get("published"):
                try:
                    published = parsedate_to_datetime(entry.published)
                except (TypeError, ValueError):
                    pass
            result.append(
                DiscoveredItem(
                    url=link,
                    title=entry.get("title", "Untitled opportunity"),
                    source_url=url,
                    summary=entry.get("summary", "Not specified / Not verified"),
                    published_at=published,
                    source_trust="discovery_only",
                )
            )
        return result
