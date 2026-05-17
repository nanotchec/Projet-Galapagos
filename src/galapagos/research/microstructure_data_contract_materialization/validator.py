from __future__ import annotations

from pathlib import Path
from typing import Any

from .materializer import ALLOWED_DATA_WRITE_ROOT, ALLOWED_FILES
from .safety_guard import MaterializationSafetyGuard

EXPECTED_SCOPE = "tiny_data_contract_materialization_ultra_bounded_no_network_no_full_dataset_no_ml_no_trading"


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors = MaterializationSafetyGuard().check(payload)["safety_issues"]
    expected = {
        "approval_source_verified": True,
        "human_approval_granted": True,
        "v1_84_authorized": True,
        "materialization_executed": True,
        "tiny_materialization_only": True,
        "full_dataset_created": False,
        "network_executed": False,
        "data_directory_writes_allowed": True,
        "data_write_approved": True,
        "unapproved_data_write_detected": False,
        "parquet_created": False,
        "csv_created": False,
        "sqlite_created": False,
        "jsonl_created": False,
        "db_created": False,
        "dataset_created": False,
        "research_dataset_updated": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "no_real_trading": True,
        "no_paper_live": True,
        "ml_signal_validation_executed": False,
        "predictions_created": False,
        "labels_created": False,
        "targets_created": False,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "clean_zip_ready_for_external_review": True,
    }
    for field, value in expected.items():
        if payload.get(field) is not value:
            errors.append(f"{field} != {value!r}")
    if payload.get("authorized_future_scope") != EXPECTED_SCOPE:
        errors.append("authorized_future_scope mismatch")
    return errors


def validate_physical_outputs(project_root: Path) -> list[str]:
    errors: list[str] = []
    allowed_root = project_root / ALLOWED_DATA_WRITE_ROOT
    allowed_paths = {project_root / path for path in ALLOWED_FILES}
    if not allowed_root.exists():
        return [f"missing allowed data root {ALLOWED_DATA_WRITE_ROOT}"]
    existing = sorted(path for path in allowed_root.glob("*") if path.is_file())
    if set(existing) != allowed_paths:
        errors.append("V1.84 data folder does not contain exactly the three authorized JSON files")
    forbidden_suffixes = {".parquet", ".csv", ".sqlite", ".jsonl", ".db"}
    for path in existing:
        if path.suffix.lower() != ".json":
            errors.append(f"non-json file in V1.84 data root: {path.name}")
        if path.suffix.lower() in forbidden_suffixes:
            errors.append(f"forbidden file type in V1.84 data root: {path.name}")
    return errors
