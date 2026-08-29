from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(slots=True)
class DiscoveredItem:
    url: str
    title: str
    source_url: str
    organization: str = "Not specified / Not verified"
    category: str = "notice"
    location: str = "Not specified / Not verified"
    eligibility: str = "Not specified / Not verified"
    stipend_salary: str = "Not specified / Not verified"
    summary: str = "Not specified / Not verified"
    published_at: datetime | None = None
    deadline: datetime | None = None
    source_trust: str = "discovery_only"
    metadata: dict[str, Any] = field(default_factory=dict)


class SourceAdapter(Protocol):
    async def discover(self, source_url: str) -> list[DiscoveredItem]: ...
