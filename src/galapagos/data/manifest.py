from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from galapagos.utils.secrets import redact_secret


@dataclass(frozen=True)
class DatasetManifest:
    dataset_id: str
    source: str
    symbol: str
    timeframe: str | None
    start_timestamp: str | None
    end_timestamp: str | None
    rows: int
    file_path: str
    data_hash: str
    downloaded_at_utc: str | None
    created_at_utc: str
    source_url_or_endpoint: str | None
    request_params_redacted: dict[str, Any]
    schema_version: str = "v1"
    data_mode: str = "research"
    causal_note: str = "Features must be joined only after available_timestamp."
    known_limitations: list[str] = field(default_factory=list)
    quality_status: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_data_hash(payload: bytes | str) -> str:
    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    return hashlib.sha256(raw).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def redact_request_params(params: dict[str, Any]) -> dict[str, Any]:
    redacted = {}
    for key, value in params.items():
        lowered = key.lower()
        if "key" in lowered or "secret" in lowered or "token" in lowered:
            redacted[key] = "configured" if value else "missing"
        elif isinstance(value, str) and len(value) > 20:
            redacted[key] = redact_secret(value)
        else:
            redacted[key] = value
    return redacted


def create_manifest(
    *,
    dataset_id: str,
    source: str,
    symbol: str,
    timeframe: str | None,
    file_path: Path,
    rows: int,
    start_timestamp: str | None = None,
    end_timestamp: str | None = None,
    source_url_or_endpoint: str | None = None,
    request_params: dict[str, Any] | None = None,
    known_limitations: list[str] | None = None,
    quality_status: str = "unknown",
) -> DatasetManifest:
    now = datetime.now(UTC).isoformat()
    data_hash = file_hash(file_path) if file_path.exists() else stable_data_hash(dataset_id)
    return DatasetManifest(
        dataset_id=dataset_id,
        source=source,
        symbol=symbol,
        timeframe=timeframe,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        rows=rows,
        file_path=str(file_path),
        data_hash=data_hash,
        downloaded_at_utc=now,
        created_at_utc=now,
        source_url_or_endpoint=source_url_or_endpoint,
        request_params_redacted=redact_request_params(request_params or {}),
        known_limitations=known_limitations or [],
        quality_status=quality_status,
    )


def write_manifest(manifest: DatasetManifest, output_dir: Path = Path("data/manifests")) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{manifest.dataset_id}.json"
    path.write_text(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path
