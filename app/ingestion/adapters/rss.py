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
            title = entry.get("title", "Untitled opportunity")
            summary = entry.get("summary", "Not specified / Not verified")
            searchable = f"{title} {summary}".lower()
            result.append(
                DiscoveredItem(
                    url=link,
                    title=title,
                    source_url=url,
                    category=_category(searchable),
                    summary=summary,
                    published_at=published,
                    source_trust="discovery_only",
                )
            )
        return result


def _category(text: str) -> str:
    if any(term in text for term in ("internship", "fellowship", "trainee", "training")):
        return "internship"
    if any(term in text for term in ("exam", "admit card", "result")):
        return "exam"
    if any(term in text for term in ("recruitment", "vacancy", "job", "career", "pharmacist")):
        return "government job"
    return "notice"
