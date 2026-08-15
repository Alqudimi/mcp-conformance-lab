"""Atomic evidence bundle writer and verifier."""

from __future__ import annotations

import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path
from tempfile import mkdtemp
from uuid import uuid4

from ..application.snapshot import snapshot_bytes, snapshot_digest
from ..domain.canonical import canonical_bytes
from ..domain.errors import EvidenceError
from ..domain.models import ContractSnapshot, Finding


class EvidenceBundleWriter:
    """Write portable, hashed evidence bundles to a local directory."""

    def write(
        self,
        directory: Path,
        target: str,
        snapshot: ContractSnapshot,
        findings: tuple[Finding, ...],
    ) -> Path:
        """Write one run atomically and return its final path."""
        directory = directory.expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
        temporary = Path(mkdtemp(prefix=f".{run_id}-", dir=directory))
        final = directory / run_id
        try:
            contract = snapshot_bytes(snapshot)
            results = canonical_bytes(
                {
                    "schema_version": 1,
                    "findings": [
                        finding.model_dump(mode="json", exclude_none=True) for finding in findings
                    ],
                }
            )
            run = canonical_bytes(
                {
                    "schema_version": 1,
                    "run_id": run_id,
                    "target": target,
                    "contract_digest": snapshot_digest(snapshot),
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
            (temporary / "contract.json").write_bytes(contract)
            (temporary / "results.json").write_bytes(results)
            (temporary / "run.json").write_bytes(run)
            files = {
                name: hashlib.sha256((temporary / name).read_bytes()).hexdigest()
                for name in ("contract.json", "results.json", "run.json")
            }
            (temporary / "manifest.sha256").write_text(
                "".join(f"{digest}  {name}\n" for name, digest in sorted(files.items())),
                encoding="utf-8",
            )
            temporary.replace(final)
            return final
        except OSError as exc:
            shutil.rmtree(temporary, ignore_errors=True)
            raise EvidenceError("could not write evidence bundle") from exc


def verify_bundle(path: Path) -> bool:
    """Verify every file listed in a bundle manifest."""
    bundle = path.expanduser().resolve()
    manifest = bundle / "manifest.sha256"
    if not manifest.is_file():
        raise EvidenceError(f"evidence manifest does not exist: {manifest}")
    try:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", maxsplit=1)
            actual = hashlib.sha256((bundle / name).read_bytes()).hexdigest()
            if actual != digest:
                return False
        return True
    except (OSError, ValueError) as exc:
        raise EvidenceError(f"could not verify evidence bundle: {bundle}") from exc
