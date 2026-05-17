from __future__ import annotations
from pathlib import Path

def validate_inputs(
    microstructure_summary: Path,
    regime_data_quality_summary: Path,
    canonical_summary: Path,
    version: str,
    additional_paths: list[Path] | None = None,
) -> dict:
    issues = []
    checked_paths = [microstructure_summary, regime_data_quality_summary, canonical_summary]
    if additional_paths:
        checked_paths.extend(additional_paths)
    for path in checked_paths:
        if not path.exists():
            issues.append(f"Missing input: {path.name}")
    
    return {
        "version": version,
        "input_guard_status": "MICROSTRUCTURE_REGIME_LABEL_INPUT_GUARD_PASSED" if not issues else "FAILED",
        "issues": issues,
        "checked_paths": [str(p) for p in checked_paths]
    }
