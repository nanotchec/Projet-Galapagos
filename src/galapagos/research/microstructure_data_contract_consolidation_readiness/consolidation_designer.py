from __future__ import annotations

from typing import Any

FUTURE_ALLOWED_ROOT = "data/research/microstructure_contract_materialization/v1_90/"
FUTURE_ALLOWED_EXTENSIONS = [".json"]
FUTURE_FORBIDDEN_EXTENSIONS = [".parquet", ".csv", ".sqlite", ".jsonl", ".db"]
FUTURE_MAX_FILES = 3
FUTURE_MAX_BYTES = 25_000


def design_consolidation_contract_v2() -> dict[str, Any]:
    """Returns a reports-only V2 contract design for a future bounded V1.90."""

    return {
        "data_contract_v2_designed": True,
        "consolidation_plan_created": True,
        "consolidation_plan_reports_only": True,
        "consolidation_plan_theoretical_paths_only": True,
        "future_consolidation_requires_v1_89_approval": True,
        "future_consolidation_allowed_root": FUTURE_ALLOWED_ROOT,
        "future_consolidation_expected_files": [
            f"{FUTURE_ALLOWED_ROOT}consolidated_manifest.json",
            f"{FUTURE_ALLOWED_ROOT}consolidated_schema_snapshot.json",
            f"{FUTURE_ALLOWED_ROOT}consolidated_quality_summary.json",
        ],
        "future_consolidation_max_files": FUTURE_MAX_FILES,
        "future_consolidation_max_bytes": FUTURE_MAX_BYTES,
        "future_consolidation_allowed_extensions": FUTURE_ALLOWED_EXTENSIONS,
        "future_consolidation_forbidden_extensions": FUTURE_FORBIDDEN_EXTENSIONS,
        "future_consolidation_no_network": True,
        "future_consolidation_no_ml": True,
        "future_consolidation_no_trading": True,
        "future_consolidation_no_full_dataset": True,
    }


def validate_consolidation_design(design: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_true = [
        "data_contract_v2_designed",
        "consolidation_plan_created",
        "consolidation_plan_reports_only",
        "consolidation_plan_theoretical_paths_only",
        "future_consolidation_requires_v1_89_approval",
        "future_consolidation_no_network",
        "future_consolidation_no_ml",
        "future_consolidation_no_trading",
        "future_consolidation_no_full_dataset",
    ]
    for field in expected_true:
        if design.get(field) is not True:
            errors.append(f"{field} != true")
    if design.get("future_consolidation_allowed_root") != FUTURE_ALLOWED_ROOT:
        errors.append("future_consolidation_allowed_root mismatch")
    if design.get("future_consolidation_max_files", 0) > FUTURE_MAX_FILES:
        errors.append("future_consolidation_max_files > 3")
    if design.get("future_consolidation_max_bytes", 0) > FUTURE_MAX_BYTES:
        errors.append("future_consolidation_max_bytes > 25000")
    if design.get("future_consolidation_allowed_extensions") != FUTURE_ALLOWED_EXTENSIONS:
        errors.append("future_consolidation_allowed_extensions mismatch")
    if design.get("future_consolidation_forbidden_extensions") != FUTURE_FORBIDDEN_EXTENSIONS:
        errors.append("future_consolidation_forbidden_extensions mismatch")
    for path in design.get("future_consolidation_expected_files", []):
        if not isinstance(path, str) or not path.startswith(FUTURE_ALLOWED_ROOT):
            errors.append("future_consolidation_expected_files contains unbounded path")
        if not str(path).endswith(".json"):
            errors.append("future_consolidation_expected_files contains non-json path")
    return errors
