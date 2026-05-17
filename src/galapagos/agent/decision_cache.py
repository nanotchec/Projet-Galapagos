from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CACHE_SCHEMA_VERSION = "decision_cache_v1_10_5"
DEFAULT_CACHE_ROOT = Path("data/decision_cache/codex_cli")


@dataclass(frozen=True)
class DecisionCacheKey:
    context_hash: str
    prompt_hash: str
    model: str
    reasoning_effort: str
    prompt_mode: str
    constraints_config_hash: str
    schema_version: str = CACHE_SCHEMA_VERSION

    @property
    def cache_key(self) -> str:
        payload = "|".join(
            [
                self.context_hash,
                self.prompt_hash,
                self.model,
                self.reasoning_effort,
                self.prompt_mode,
                self.constraints_config_hash,
                self.schema_version,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, str]:
        payload = asdict(self)
        payload["cache_key"] = self.cache_key
        return payload


@dataclass(frozen=True)
class DecisionCacheEntry:
    cache_key: str
    context_hash: str
    prompt_hash: str
    model: str
    reasoning_effort: str
    prompt_mode: str
    constraints_config_hash: str
    created_at_utc: str
    provider_name: str
    raw_response: str
    parsed_decision: dict[str, Any]
    decision_validity: str
    parser_repair_applied: bool
    postprocessing_warnings: list[str]
    safety_warnings: list[str]
    duration_seconds: float
    codex_exit_code: int | None
    stdout_preview: str
    stderr_preview: str
    source: str = "codex_cli"
    schema_version: str = CACHE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DecisionCacheEntry:
        return cls(
            cache_key=str(payload["cache_key"]),
            context_hash=str(payload["context_hash"]),
            prompt_hash=str(payload["prompt_hash"]),
            model=str(payload["model"]),
            reasoning_effort=str(payload["reasoning_effort"]),
            prompt_mode=str(payload["prompt_mode"]),
            constraints_config_hash=str(payload["constraints_config_hash"]),
            created_at_utc=str(payload["created_at_utc"]),
            provider_name=str(payload.get("provider_name") or "codex_cli"),
            raw_response=str(payload.get("raw_response") or ""),
            parsed_decision=dict(payload.get("parsed_decision") or {}),
            decision_validity=str(payload.get("decision_validity") or "unknown"),
            parser_repair_applied=bool(payload.get("parser_repair_applied", False)),
            postprocessing_warnings=list(payload.get("postprocessing_warnings") or []),
            safety_warnings=list(payload.get("safety_warnings") or []),
            duration_seconds=float(payload.get("duration_seconds") or 0.0),
            codex_exit_code=payload.get("codex_exit_code"),
            stdout_preview=str(payload.get("stdout_preview") or ""),
            stderr_preview=str(payload.get("stderr_preview") or ""),
            source=str(payload.get("source") or "codex_cli"),
            schema_version=str(payload.get("schema_version") or CACHE_SCHEMA_VERSION),
        )


class DecisionCache:
    def __init__(self, root: str | Path = DEFAULT_CACHE_ROOT) -> None:
        self.root = Path(root)
        self.entries_dir = self.root / "entries"
        self.index_path = self.root / "index.jsonl"

    def get(self, key: DecisionCacheKey) -> DecisionCacheEntry | None:
        path = self._entry_path(key.cache_key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        entry = DecisionCacheEntry.from_dict(payload)
        if not self._entry_matches_key(entry, key):
            return None
        return entry

    def put(self, key: DecisionCacheKey, entry: DecisionCacheEntry) -> Path:
        if entry.cache_key != key.cache_key:
            raise ValueError("Decision cache entry key does not match computed key.")
        self.entries_dir.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._entry_path(key.cache_key)
        payload = entry.to_dict()
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_index_record(payload), ensure_ascii=False) + "\n")
        return path

    def refresh(self, key: DecisionCacheKey, entry: DecisionCacheEntry) -> Path:
        return self.put(key, entry)

    def _entry_path(self, cache_key: str) -> Path:
        return self.entries_dir / f"{cache_key}.json"

    @staticmethod
    def _entry_matches_key(entry: DecisionCacheEntry, key: DecisionCacheKey) -> bool:
        return (
            entry.context_hash == key.context_hash
            and entry.prompt_hash == key.prompt_hash
            and entry.model == key.model
            and entry.reasoning_effort == key.reasoning_effort
            and entry.prompt_mode == key.prompt_mode
            and entry.constraints_config_hash == key.constraints_config_hash
            and entry.schema_version == key.schema_version
        )


def build_decision_cache_key(
    *,
    context_hash: str,
    prompt_hash: str,
    model: str,
    reasoning_effort: str,
    prompt_mode: str,
    constraints_config_hash: str,
) -> DecisionCacheKey:
    return DecisionCacheKey(
        context_hash=context_hash,
        prompt_hash=prompt_hash,
        model=model,
        reasoning_effort=reasoning_effort,
        prompt_mode=prompt_mode,
        constraints_config_hash=constraints_config_hash,
    )


def stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _index_record(payload: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "cache_key",
        "context_hash",
        "prompt_hash",
        "model",
        "reasoning_effort",
        "prompt_mode",
        "constraints_config_hash",
        "created_at_utc",
        "provider_name",
        "decision_validity",
        "duration_seconds",
        "source",
        "schema_version",
    ]
    return {key: payload.get(key) for key in keys}
