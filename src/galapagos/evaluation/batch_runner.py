from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_CHECKPOINT_DIR = Path("data/checkpoints")


def save_checkpoint(
    run_id: str,
    completed_items: list[dict[str, Any]],
    pending_items: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    *,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
    quota_limited: bool = False,
) -> Path:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "updated_at_utc": datetime.now(UTC).isoformat(),
        "completed_items": completed_items,
        "pending_items": pending_items,
        "failures": failures,
        "quota_limited": quota_limited,
        "max_concurrency_default": 1,
        "notes": [
            "Chaque decision GPT future doit etre ecrite dans le decision cache des obtention.",
            "La reprise doit traiter uniquement pending_items.",
        ],
    }
    path = checkpoint_dir / f"{run_id}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_checkpoint(
    run_id: str,
    *,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
) -> dict[str, Any]:
    path = checkpoint_dir / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found for run_id={run_id}.")
    return json.loads(path.read_text(encoding="utf-8"))


def resume_run(
    run_id: str,
    *,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
) -> dict[str, Any]:
    checkpoint = load_checkpoint(run_id, checkpoint_dir=checkpoint_dir)
    return {
        "run_id": run_id,
        "pending_items": checkpoint.get("pending_items", []),
        "completed_count": len(checkpoint.get("completed_items", [])),
        "failure_count": len(checkpoint.get("failures", [])),
        "quota_limited": bool(checkpoint.get("quota_limited", False)),
        "max_concurrency": 1,
    }


def mark_quota_limited(
    run_id: str,
    *,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
) -> Path:
    checkpoint = load_checkpoint(run_id, checkpoint_dir=checkpoint_dir)
    return save_checkpoint(
        run_id,
        completed_items=list(checkpoint.get("completed_items", [])),
        pending_items=list(checkpoint.get("pending_items", [])),
        failures=list(checkpoint.get("failures", [])),
        checkpoint_dir=checkpoint_dir,
        quota_limited=True,
    )


def stop_gracefully_on_quota_error(
    run_id: str,
    completed_items: list[dict[str, Any]],
    pending_items: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    *,
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR,
) -> dict[str, Any]:
    path = save_checkpoint(
        run_id,
        completed_items=completed_items,
        pending_items=pending_items,
        failures=failures,
        checkpoint_dir=checkpoint_dir,
        quota_limited=True,
    )
    return {
        "status": "quota_limited",
        "checkpoint_path": str(path),
        "completed_count": len(completed_items),
        "pending_count": len(pending_items),
        "failure_count": len(failures),
    }
