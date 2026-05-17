"""Input guard for the payoff-objective failure diagnostic."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def build_failure_input_guard(inputs: dict[str, Any], *, version: str) -> dict[str, Any]:
    payoff_summary = inputs["payoff_summary"]
    canonical_summary = inputs["canonical_summary"]
    diagnostic_summary = inputs["diagnostic_summary"]
    paths = inputs.get("paths", {})
    issues: list[str] = []

    def _summary_count(summary: dict[str, Any], primary: str, fallback: str) -> int:
        value = summary.get(primary, summary.get(fallback, 0))
        return int(value)

    for key, value in paths.items():
        lowered = str(value).lower()
        if any(token in lowered for token in ["mock", "scratch", "/dev/null"]):
            issues.append(f"mock/scratch path detected in {key}")
    if payoff_summary.get("version") != "V1.40.1":
        issues.append("payoff_objective_base_version must be V1.40.1")
    if payoff_summary.get("diagnostic_base") != "V1.39":
        issues.append("diagnostic_base must be V1.39")
    if payoff_summary.get("canonical_base_version") != "V1.37.2":
        issues.append("canonical_base_version must be V1.37.2")
    if payoff_summary.get("research_base_version") != "V1.38.4":
        issues.append("research_base_version must be V1.38.4")
    if payoff_summary.get("split_integrity_status") != "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED":
        issues.append("split_integrity_status must be PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED")
    if int(payoff_summary.get("invalid_split_count", -1)) != 0:
        issues.append("invalid_split_count must be zero")
    if _summary_count(payoff_summary, "selected_count_total", "selected_count_total_v1_39") != 129527:
        issues.append("selected_count_total must be 129527")
    if _summary_count(payoff_summary, "selected_count_2026", "selected_count_2026_v1_39") != 19497:
        issues.append("selected_count_2026 must be 19497")
    if int(canonical_summary.get("raw_prediction_rows", -1)) != 171648:
        issues.append("raw_prediction_rows must be 171648")
    if int(canonical_summary.get("selection_dataset_rows", -1)) != 171648:
        issues.append("selection_dataset_rows must be 171648")
    if int(canonical_summary.get("outcome_dataset_rows", -1)) != 171648:
        issues.append("outcome_dataset_rows must be 171648")
    if int(canonical_summary.get("opportunity_index_rows", -1)) != 171648:
        issues.append("opportunity_index_rows must be 171648")
    if payoff_summary.get("best_candidate_observed") != "asymmetric_loss_weighted_classifier":
        issues.append("best_candidate_observed mismatch")
    if payoff_summary.get("recent_window_status") != "RECENT_WINDOW_WEAK":
        issues.append("recent_window_status mismatch")
    if payoff_summary.get("final_verdict") != "PAYOFF_OBJECTIVE_RESEARCH_RECENT_WINDOW_WEAK":
        issues.append("final_verdict mismatch")
    if diagnostic_summary.get("version") != "V1.39":
        issues.append("diagnostic summary version mismatch")
    if diagnostic_summary.get("final_verdict") != "EV_DEGRADATION_MULTI_FACTOR":
        issues.append("diagnostic summary verdict mismatch")
    primary_driver = diagnostic_summary.get(
        "primary_failure_driver",
        diagnostic_summary.get("primary_degradation_driver"),
    )
    if primary_driver != "EV_PROXY_OVERESTIMATES_2026":
        issues.append("diagnostic summary primary driver mismatch")
    if any(any(token in str(value).lower() for token in ["mock", "scratch", "/dev/null"]) for value in paths.values()):
        issues.append("mock/scratch path detected")
    status = "PAYOFF_OBJECTIVE_FAILURE_INPUT_GUARD_PASSED" if not issues else "PAYOFF_OBJECTIVE_FAILURE_INPUT_GUARD_FAILED"
    return {
        "version": version.upper(),
        "payoff_objective_base_version": payoff_summary.get("version"),
        "diagnostic_base": payoff_summary.get("diagnostic_base"),
        "canonical_base_version": payoff_summary.get("canonical_base_version"),
        "research_base_version": payoff_summary.get("research_base_version"),
        "input_paths_status": "REAL_DATA_ONLY" if not issues else "INVALID_INPUT_PATHS",
        "mock_data_detected": bool(issues and any("mock/scratch" in issue for issue in issues)),
        "raw_prediction_rows": int(canonical_summary.get("raw_prediction_rows", 0)),
        "selection_dataset_rows": int(canonical_summary.get("selection_dataset_rows", 0)),
        "outcome_dataset_rows": int(canonical_summary.get("outcome_dataset_rows", 0)),
        "opportunity_index_rows": int(canonical_summary.get("opportunity_index_rows", 0)),
        "selected_count_total_v1_39": _summary_count(payoff_summary, "selected_count_total", "selected_count_total_v1_39"),
        "selected_count_2026_v1_39": _summary_count(payoff_summary, "selected_count_2026", "selected_count_2026_v1_39"),
        "split_integrity_status": payoff_summary.get("split_integrity_status"),
        "invalid_split_count": int(payoff_summary.get("invalid_split_count", 0)),
        "best_candidate_observed": payoff_summary.get("best_candidate_observed"),
        "recent_window_status": payoff_summary.get("recent_window_status"),
        "final_verdict": payoff_summary.get("final_verdict"),
        "v1_39_final_verdict": diagnostic_summary.get("final_verdict"),
        "v1_39_primary_degradation_driver": diagnostic_summary.get("primary_degradation_driver"),
        "failure_input_guard_status": status,
        "issues": issues,
    }
