from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from galapagos.utils.paths import project_path


def load_yaml(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = project_path(str(file_path))
    with file_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def load_profile(profile_name: str) -> dict[str, Any]:
    if profile_name in {"30m", "galapagos_30m"}:
        return load_yaml("configs/galapagos_30m.yaml")
    if profile_name in {"4h", "galapagos_4h"}:
        return load_yaml("configs/galapagos_4h.yaml")
    raise ValueError(f"Unknown profile: {profile_name}")

