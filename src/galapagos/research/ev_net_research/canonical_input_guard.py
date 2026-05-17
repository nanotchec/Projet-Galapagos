"""Canonical EV-net input guard for V1.38."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CANONICAL_VERSION = "V1.37.2"
EXPECTED_ROWS = 171648
EXPECTED_ROWS_2026 = 24360
EXPECTED_SELECTION_STATUS = "CANONICAL_SELECTION_DATASET_CLEAN"
EXPECTED_OUTCOME_STATUS = "CANONICAL_OUTCOME_DATASET_SEPARATED"
EXPECTED_INDEX_STATUS = "CANONICAL_OPPORTUNITY_INDEX_DEFINED"
EXPECTED_INPUT_PATH_STATUS = "CANONICAL_INPUT_PATH_GUARD_PASSED"
EXPECTED_COUNT_STATUS = "CANONICAL_COUNT_SANITY_GUARD_PASSED"
EXPECTED_CONSISTENCY_STATUS = "CANONICAL_UNIVERSE_REPORTS_CONSISTENT_REAL_DATA_FORMAL_SPLIT"
EXPECTED_WARNING_STATUS = "CANONICAL_INPUT_OUTCOME_WARNING_RESOLVED"


def audit_canonical_input_guard(
    *,
    canonical_summary_path: str | Path,
    canonical_consistency_path: str | Path,
    predictions_path: str | Path,
    dataset_path: str | Path,
    intrabar_path: str | Path,
) -> dict[str, Any]:
    """Validate that the canonical V1.37.2 base is present and real-data aligned."""
    summary_path = Path(canonical_summary_path)
    consistency_path = Path(canonical_consistency_path)
    pred_path = Path(predictions_path)
    ds_path = Path(dataset_path)
    intrabar_file = Path(intrabar_path)

    issues: list[str] = []
    path_checks = {
        "predictions_path": _check_real_path(pred_path),
        "dataset_path": _check_real_path(ds_path),
        "intrabar_path": _check_real_path(intrabar_file),
    }
    if not summary_path.exists():
        issues.append(f"Missing canonical summary: {summary_path}")
    if not consistency_path.exists():
        issues.append(f"Missing canonical consistency report: {consistency_path}")
    if not pred_path.exists():
        issues.append(f"Missing predictions file: {pred_path}")
    if not ds_path.exists():
        issues.append(f"Missing dataset file: {ds_path}")
    if not intrabar_file.exists():
        issues.append(f"Missing intrabar file: {intrabar_file}")

    summary = _load_json(summary_path) if summary_path.exists() else {}
    consistency = _load_json(consistency_path) if consistency_path.exists() else {}

    counts = {
        "raw_prediction_rows": int(summary.get("raw_prediction_rows", 0)),
        "selection_dataset_rows": int(summary.get("selection_dataset_rows", 0)),
        "outcome_dataset_rows": int(summary.get("outcome_dataset_rows", 0)),
        "opportunity_index_rows": int(summary.get("opportunity_index_rows", 0)),
        "raw_prediction_rows_2026": int(summary.get("raw_prediction_rows_2026", 0)),
        "selection_dataset_rows_2026": int(summary.get("selection_dataset_rows_2026", 0)),
        "outcome_dataset_rows_2026": int(summary.get("outcome_dataset_rows_2026", 0)),
        "opportunity_index_rows_2026": int(summary.get("opportunity_index_rows_2026", 0)),
    }

    version_value = summary.get("version", summary.get("universe_version"))
    if version_value != CANONICAL_VERSION:
        issues.append(f"canonical summary version mismatch: {version_value}")
    if summary.get("final_verdict") != "CANONICAL_UNIVERSE_DEFINED_WITH_REAL_DATA_SELECTION_OUTCOME_SPLIT":
        issues.append(f"canonical summary final_verdict mismatch: {summary.get('final_verdict')}")
    if summary.get("consistency_check_status") != EXPECTED_CONSISTENCY_STATUS:
        issues.append(
            f"canonical summary consistency_check_status mismatch: "
            f"{summary.get('consistency_check_status')}"
        )
    if summary.get("input_path_guard_status") != EXPECTED_INPUT_PATH_STATUS:
        issues.append(f"input_path_guard_status mismatch: {summary.get('input_path_guard_status')}")
    if summary.get("count_sanity_guard_status") != EXPECTED_COUNT_STATUS:
        issues.append(f"count_sanity_guard_status mismatch: {summary.get('count_sanity_guard_status')}")
    if summary.get("selection_dataset_status") != EXPECTED_SELECTION_STATUS:
        issues.append(f"selection_dataset_status mismatch: {summary.get('selection_dataset_status')}")
    if summary.get("outcome_dataset_status") != EXPECTED_OUTCOME_STATUS:
        issues.append(f"outcome_dataset_status mismatch: {summary.get('outcome_dataset_status')}")
    if summary.get("opportunity_index_status") != EXPECTED_INDEX_STATUS:
        issues.append(f"opportunity_index_status mismatch: {summary.get('opportunity_index_status')}")
    if summary.get("warning_resolution_status") != EXPECTED_WARNING_STATUS:
        issues.append(
            f"warning_resolution_status mismatch: {summary.get('warning_resolution_status')}"
        )
    if summary.get("warnings_present") is not False:
        issues.append("warnings_present must be false")
    if summary.get("no_real_trading") is not True:
        issues.append("no_real_trading must be true")
    if summary.get("holdout_executed") is not False:
        issues.append("holdout_executed must be false")
    codex_called = summary.get("codex_cli_called")
    if codex_called not in (False, None):
        issues.append("codex_cli_called must be false")
    if counts["raw_prediction_rows"] != EXPECTED_ROWS:
        issues.append(f"raw_prediction_rows mismatch: {counts['raw_prediction_rows']}")
    if counts["selection_dataset_rows"] != EXPECTED_ROWS:
        issues.append(f"selection_dataset_rows mismatch: {counts['selection_dataset_rows']}")
    if counts["outcome_dataset_rows"] != EXPECTED_ROWS:
        issues.append(f"outcome_dataset_rows mismatch: {counts['outcome_dataset_rows']}")
    if counts["opportunity_index_rows"] != EXPECTED_ROWS:
        issues.append(f"opportunity_index_rows mismatch: {counts['opportunity_index_rows']}")
    if counts["raw_prediction_rows_2026"] != EXPECTED_ROWS_2026:
        issues.append(
            f"raw_prediction_rows_2026 mismatch: {counts['raw_prediction_rows_2026']}"
        )

    guard_status = "EV_NET_CANONICAL_INPUT_GUARD_PASSED" if not issues else "EV_NET_CANONICAL_INPUT_GUARD_FAILED"
    return {
        "canonical_base_version": CANONICAL_VERSION,
        "guard_status": guard_status,
        "input_path_guard_status": summary.get("input_path_guard_status", "MISSING"),
        "count_sanity_guard_status": summary.get("count_sanity_guard_status", "MISSING"),
        "selection_dataset_status": summary.get("selection_dataset_status", "MISSING"),
        "outcome_dataset_status": summary.get("outcome_dataset_status", "MISSING"),
        "opportunity_index_status": summary.get("opportunity_index_status", "MISSING"),
        "consistency_check_status": summary.get("consistency_check_status", "MISSING"),
        "raw_prediction_rows": counts["raw_prediction_rows"],
        "raw_prediction_rows_2026": counts["raw_prediction_rows_2026"],
        "selection_dataset_rows": counts["selection_dataset_rows"],
        "selection_dataset_rows_2026": counts["selection_dataset_rows_2026"],
        "outcome_dataset_rows": counts["outcome_dataset_rows"],
        "outcome_dataset_rows_2026": counts["outcome_dataset_rows_2026"],
        "opportunity_index_rows": counts["opportunity_index_rows"],
        "opportunity_index_rows_2026": counts["opportunity_index_rows_2026"],
        "real_data_enforced": all(item["real_data_enforced"] for item in path_checks.values()),
        "mock_data_detected": any(not item["real_data_enforced"] for item in path_checks.values())
        or any(_looks_mock_or_scratch(path) for path in [pred_path, ds_path, intrabar_file]),
        "path_checks": path_checks,
        "issues": issues,
    }


def _check_real_path(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "real_data_enforced": not _looks_mock_or_scratch(path),
    }


def _looks_mock_or_scratch(path: Path) -> bool:
    lowered = str(path).lower()
    forbidden_tokens = [
        "mock",
        "scratch",
        "/dev/null",
        "tmp",
        ".gemini/antigravity/brain",
    ]
    return any(token in lowered for token in forbidden_tokens)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
