"""Stable identities and timezone-aware chronology, independent of a model."""
from datetime import datetime, timezone
import hashlib
import json


class MemoryError(ValueError):
    """A publication or lookup violates the memory contract."""


def canonical_json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MemoryError("memory:invalid_json") from exc


def content_sha256(value):
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def at(value):
    if not isinstance(value, str) or not value.strip():
        raise MemoryError("memory:timestamp_required")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise MemoryError("memory:invalid_timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise MemoryError("memory:timezone_required")
    return parsed.astimezone(timezone.utc)


def nonempty(value, name):
    if not isinstance(value, str) or not value.strip():
        raise MemoryError("memory:invalid_" + name)
    return value
