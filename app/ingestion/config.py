from pathlib import Path
from typing import Any

import yaml


def load_yaml(name: str) -> dict[str, Any]:
    path = Path(__file__).resolve().parents[2] / "config" / name
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data if isinstance(data, dict) else {}


def load_sources() -> list[dict[str, Any]]:
    sources = load_yaml("default_sources.yaml").get("sources", [])
    return [source for source in sources if isinstance(source, dict) and source.get("url")]


def load_terms() -> tuple[str, ...]:
    keywords = load_yaml("default_keywords.yaml")
    roles = keywords.get("roles", [])
    generic = (
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
        "admit card",
        "notification",
        "career opportunity",
    )
    return tuple(
        dict.fromkeys(
            [str(role).strip() for role in roles if str(role).strip()] + list(generic)
        )
    )
