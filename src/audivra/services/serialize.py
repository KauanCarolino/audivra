"""Convert Python and Django values into JSON-safe data."""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID


def to_jsonable(value: Any) -> Any:
    """Return a value that Django's JSONField can store."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (str, int, float)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if hasattr(value, "_meta") and hasattr(value, "pk"):
        return to_jsonable(value.pk)
    return str(value)
