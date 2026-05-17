from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HOLDOUT_WARNING = "Do not tune on this result."


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def mark_holdout_used(
    output_dir: str | Path,
    *,
    config_hash: str,
    prompt_hash: str,
    code_version: str | None = None,
) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / "HOLDOUT_USED.txt"
    previous_warning = ""
    if marker.exists():
        text = marker.read_text(encoding="utf-8")
        if config_hash not in text or prompt_hash not in text:
            previous_warning = (
                "\nWARNING: holdout was already used with a different config or prompt. "
                "Create a new holdout before tuning.\n"
            )
    content = "\n".join(
        [
            "Galapagos holdout usage marker",
            f"created_at_utc: {datetime.now(UTC).isoformat()}",
            f"config_hash: {config_hash}",
            f"prompt_hash: {prompt_hash}",
            f"code_version: {code_version or _code_version()}",
            f"warning: {HOLDOUT_WARNING}",
            (
                "Ne pas modifier le prompt apres avoir regarde le holdout, "
                "sauf a creer un nouveau holdout."
            ),
            previous_warning.strip(),
        ]
    ).strip()
    marker.write_text(content + "\n", encoding="utf-8")
    return marker


def _code_version() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:  # noqa: BLE001
        return "not_available"
    value = completed.stdout.strip()
    return value or "not_available"
