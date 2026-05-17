from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_loss_report(
    name: str, payload: dict[str, Any] | str, output_dir: str = "reports/research"
) -> Path:
    """Save a loss attribution report as JSON or MD."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    if isinstance(payload, dict):
        file_path = out_path / f"{name}.json"
        with open(file_path, "w") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    else:
        file_path = out_path / f"{name}.md"
        with open(file_path, "w") as f:
            f.write(payload)
    
    return file_path
