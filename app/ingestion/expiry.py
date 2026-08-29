from datetime import UTC, datetime


def expiry_status(deadline: datetime | None, now: datetime | None = None) -> str:
    if deadline is None:
        return "UNKNOWN"
    now = now or datetime.now(UTC)
    remaining = (deadline - now).total_seconds()
    if remaining < 0:
        return "EXPIRED"
    if remaining <= 3 * 86400:
        return "EXPIRING_SOON"
    return "ACTIVE"
