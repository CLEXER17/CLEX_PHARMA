from collections.abc import Awaitable, Callable
from urllib.parse import urljoin, urlsplit, urlunsplit

from selectolax.parser import HTMLParser, Node

from app.ingestion.adapters.base import DiscoveredItem
from app.ingestion.security import validate_external_url

ACTIONABLE_SIGNALS = (
    "b.pharm",
    "b pharm",
    "pharmacy",
    "pharmaceutical",
    "pharmacist",
    "drug inspector",
    "recruitment",
    "vacancy",
    "job opening",
    "internship",
    "fellowship",
    "trainee",
    "training",
    "admit card",
    "exam",
    "examination",
    "result",
    "notification",
    "career opportunity",
)
NAVIGATION_TAGS = {"nav", "header", "footer"}
GENERIC_LABELS = {
    "about",
    "about us",
    "academic courses",
    "contact",
    "contact us",
    "find international jobs e-migrate",
    "government jobs",
    "home",
    "key dates",
    "jobs for women",
    "jobs for differently abled",
    "jobs for ex-servicemen",
    "participate in job fairs and events",
    "support",
    "view details",
}
EXCLUDED_SIGNALS = {"syllabus", "tender", "procurement", "annual report"}
Fetcher = Callable[[str], Awaitable[str]]


class HTMLAdapter:
    """Discover relevant, visible links from a permitted public HTML page."""

    def __init__(self, fetcher: Fetcher, terms: tuple[str, ...] = ACTIONABLE_SIGNALS):
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
            if not self._same_host(url, candidate) or self._inside_navigation(anchor):
                continue
            link = self._canonical_link(validate_external_url(candidate))
            if link in seen:
                continue
            text = self._clean_text(anchor.text(separator=" ", strip=True))
            path_text = urlsplit(link).path.replace("-", " ").replace("_", " ").lower()
            searchable = f"{text} {path_text}".strip().lower()
            if not self._is_relevant(text, searchable):
                continue
            seen.add(link)
            summary = self._local_context(anchor) or text
            title = text if text.lower() not in GENERIC_LABELS else self._path_title(path_text)
            result.append(
                DiscoveredItem(
                    url=link,
                    title=title[:500],
                    source_url=url,
                    organization=organization,
                    category=self._category(searchable),
                    summary=summary[:2000] or "Not specified / Not verified",
                    source_trust=source_trust,
                )
            )
        return result

    def _is_relevant(self, text: str, searchable: str) -> bool:
        if not text:
            return False
        if any(signal in searchable for signal in EXCLUDED_SIGNALS):
            return False
        if text.lower() in GENERIC_LABELS and not any(
            term in searchable for term in self.terms
        ):
            return False
        return any(term in searchable for term in self.terms)

    @staticmethod
    def _clean_text(value: str) -> str:
        return " ".join(value.split())

    @classmethod
    def _local_context(cls, anchor: Node) -> str:
        node = anchor.parent
        while node is not None and node.tag not in {"body", "html"}:
            if node.tag in {"li", "article", "p", "tr"}:
                return cls._clean_text(node.text(separator=" ", strip=True))
            node = node.parent
        return ""

    @staticmethod
    def _inside_navigation(anchor: Node) -> bool:
        node = anchor.parent
        while node is not None and node.tag not in {"body", "html"}:
            if node.tag in NAVIGATION_TAGS:
                return True
            classes = (node.attributes.get("class") or "").lower()
            node_id = (node.attributes.get("id") or "").lower()
            if any(
                token in f"{classes} {node_id}"
                for token in ("nav", "menu", "header", "footer")
            ):
                return True
            node = node.parent
        return False

    @staticmethod
    def _path_title(path_text: str) -> str:
        words = path_text.strip(" /").split()
        return " ".join(words[-4:]).title() if words else "Official opportunity notice"

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
        if any(term in text for term in ("internship", "fellowship", "trainee", "training")):
            return "internship"
        if any(term in text for term in ("exam", "admit card", "result")):
            return "exam"
        if any(term in text for term in ("recruitment", "vacancy", "job", "career", "pharmacist")):
            return "government job"
        return "notice"


HTMLSourceAdapter = HTMLAdapter
