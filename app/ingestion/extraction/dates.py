from datetime import datetime

from dateutil import parser


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parser.parse(value, fuzzy=True)
    except (ValueError, OverflowError):
        return None
