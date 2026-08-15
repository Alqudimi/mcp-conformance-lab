"""Contract snapshot normalization and digesting."""

from __future__ import annotations

from typing import Any

from ..domain.canonical import canonical_bytes, sha256_digest
from ..domain.models import ContractSnapshot


def canonical_snapshot_payload(snapshot: ContractSnapshot) -> dict[str, Any]:
    """Return a stable JSON-compatible snapshot payload."""
    payload = snapshot.model_dump(mode="json", exclude_none=True)
    payload["tools"] = sorted(payload.get("tools", []), key=lambda item: item["name"])
    payload["resources"] = sorted(payload.get("resources", []), key=lambda item: item["uri"])
    payload["prompts"] = sorted(payload.get("prompts", []), key=lambda item: item["name"])
    for prompt in payload["prompts"]:
        prompt["arguments"] = sorted(prompt.get("arguments", []), key=lambda item: item["name"])
    return payload


def snapshot_digest(snapshot: ContractSnapshot) -> str:
    """Compute the digest of the normalized contract snapshot."""
    return sha256_digest(canonical_snapshot_payload(snapshot))


def snapshot_bytes(snapshot: ContractSnapshot) -> bytes:
    """Serialize the normalized contract snapshot to canonical bytes."""
    return canonical_bytes(canonical_snapshot_payload(snapshot))
