from rapidfuzz.fuzz import ratio


def is_duplicate(
    existing_title: str, existing_org: str, title: str, organization: str, threshold: int = 88
) -> bool:
    if existing_org.strip().lower() != organization.strip().lower():
        return False
    return ratio(existing_title.lower(), title.lower()) >= threshold
