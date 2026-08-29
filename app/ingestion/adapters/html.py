from collections.abc import Awaitable, Callable
from urllib.parse import urljoin, urlsplit, urlunsplit

from selectolax.parser import HTMLParser

from app.ingestion.adapters.base import DiscoveredItem
from app.ingestion.security import validate_external_url

DEFAULT_TERMS = (
    "b.pharm",
    "b pharm",
    "pharmacy",
    "pharmaceutical",
    "pharmacist",
    "drug inspector",
    "recruitment",
    "vacancy",
    "job",
    "internship",
    "fellowship",
    "exam",
    "admit card",
    "result",
    "notification",
    "career",
)
Fetcher = Callable[[str], Awaitable[str]]


class HTMLAdapter:
    """Discover relevant, visible links from a permitted public HTML page."""

    def __init__(self, fetcher: Fetcher, terms: tuple[str, ...] = DEFAULT_TERMS):
        self.fetcher = fetcher
        self.terms = tuple(term.lower() for term in terms if term.strip())

    async def discover(
        self,
        source_url: str,
        *,
        organization: str = "Not specified / Not verified",
        source_trust: str = "discovery_only",
    ) -> list[DiscoveredItem]:
        url = validate_external_url(source_url)
        body = await self.fetcher(url)
        tree = HTMLParser(body)
        result: list[DiscoveredItem] = []
        seen: set[str] = set()
        for anchor in tree.css("a[href]"):
            href = (anchor.attributes.get("href") or "").strip()
            if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
                continue
            candidate = urljoin(url, href)
            if not self._same_host(url, candidate):
                continue
            link = self._canonical_link(validate_external_url(candidate))
            if link in seen:
                continue
            text = " ".join(anchor.text(separator=" ", strip=True).split())
            parent = anchor.parent
            nearby = (
                " ".join(parent.text(separator=" ", strip=True).split())
                if parent and parent.tag not in {"body", "html"}
                else text
            )
            searchable = f"{text} {nearby} {urlsplit(link).path}".lower()
            if not text or not any(term in searchable for term in self.terms):
                continue
            seen.add(link)
            result.append(
                DiscoveredItem(
                    url=link,
                    title=text[:500],
                    source_url=url,
                    organization=organization,
                    category=self._category(searchable),
                    summary=nearby[:2000] or "Not specified / Not verified",
                    source_trust=source_trust,
                )
            )
        return result

    @staticmethod
    def _canonical_link(url: str) -> str:
        parts = urlsplit(url)
        return urlunsplit(
            (parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, "")
        )

    @staticmethod
    def _same_host(source_url: str, link: str) -> bool:
        return urlsplit(source_url).netloc.lower() == urlsplit(link).netloc.lower()

    @staticmethod
    def _category(text: str) -> str:
        if any(term in text for term in ("internship", "fellowship", "trainee")):
            return "internship"
        if any(term in text for term in ("exam", "admit card", "result")):
            return "exam"
        if any(term in text for term in ("recruitment", "vacancy", "job", "career")):
            return "government job"
        return "notice"


HTMLSourceAdapter = HTMLAdapter
