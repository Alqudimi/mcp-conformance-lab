"""Stable JSON serialization and digest helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel


def canonical_bytes(value: BaseModel | dict[str, Any] | list[Any]) -> bytes:
    """Serialize JSON-compatible data deterministically as UTF-8 bytes."""
    if isinstance(value, BaseModel):
        payload: Any = value.model_dump(mode="json", exclude_none=True)
    else:
        payload = value
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_digest(value: BaseModel | dict[str, Any] | list[Any] | bytes) -> str:
    """Return the lowercase SHA-256 digest for canonical content."""
    content = value if isinstance(value, bytes) else canonical_bytes(value)
    return hashlib.sha256(content).hexdigest()
