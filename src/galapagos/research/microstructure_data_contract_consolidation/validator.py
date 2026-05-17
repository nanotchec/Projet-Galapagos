from __future__ import annotations

from pathlib import Path
from typing import Any

from .consolidator import ALLOWED_DATA_WRITE_ROOT, ALLOWED_FILES
from .safety_guard import ConsolidationSafetyGuard

EXPECTED_SCOPE = "tiny_data_contract_consolidation_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading"


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors = ConsolidationSafetyGuard().check(payload)["safety_issues"]
    if payload.get("authorized_future_scope") != EXPECTED_SCOPE:
        errors.append("authorized_future_scope mismatch")
    for field in ["approval_source_verified", "human_approval_granted", "v1_90_authorized"]:
        if payload.get(field) is not True:
            errors.append(f"{field} != true")
    for field in ["network_executed", "dataset_created", "trading_allowed", "real_orders_possible"]:
        if payload.get(field) is not False:
            errors.append(f"{field} != false")
    for field in ["release_ready_for_external_review", "smoke_test_passed", "clean_zip_ready_for_external_review"]:
        if payload.get(field) is not True:
            errors.append(f"{field} != true")
    return errors


def validate_physical_outputs(project_root: Path) -> list[str]:
    errors: list[str] = []
    allowed_root = project_root / ALLOWED_DATA_WRITE_ROOT
    allowed_paths = {project_root / path for path in ALLOWED_FILES}
    if not allowed_root.exists():
        return [f"missing allowed data root {ALLOWED_DATA_WRITE_ROOT}"]
    existing = sorted(path for path in allowed_root.glob("*") if path.is_file())
    if set(existing) != allowed_paths:
        errors.append("V1.90 data folder does not contain exactly the three authorized JSON files")
    for path in existing:
        if path.suffix.lower() != ".json":
            errors.append(f"non-json file in V1.90 data root: {path.name}")
        if path.suffix.lower() in {".parquet", ".csv", ".sqlite", ".jsonl", ".db"}:
            errors.append(f"forbidden file type in V1.90 data root: {path.name}")
    return errors
