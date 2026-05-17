from __future__ import annotations

from typing import Any

from .approval_gate import AUTHORIZED_FUTURE_SCOPE
from .consolidation_designer import validate_consolidation_design


EXPECTED_TRUE = [
    "readiness_pack_executed",
    "consolidation_design_executed",
    "approval_gate_only",
    "reports_only",
    "no_new_data_directory_writes",
    "no_strategy_validated",
    "no_paper_live",
    "no_real_trading",
    "v1_84_hashes_verified",
    "v1_87_hashes_verified",
    "v1_84_json_valid",
    "v1_87_json_valid",
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

EXPECTED_FALSE = [
    "consolidation_executed",
    "data_contract_actual_write_executed",
    "materialization_executed",
    "new_materialization_executed",
    "scope_drift_detected",
    "data_directory_writes_allowed",
    "data_directory_write_attempted",
    "new_data_files_created",
    "existing_data_files_modified",
    "existing_v1_84_files_modified",
    "existing_v1_87_files_modified",
    "dataset_created",
    "research_dataset_updated",
    "forbidden_file_types_detected",
    "parquet_created",
    "csv_created",
    "sqlite_created",
    "jsonl_created",
    "db_created",
    "network_executed",
    "new_network_requests_executed",
    "pagination_used",
    "authenticated_request_allowed",
    "secrets_used",
    "strategy_link_allowed",
    "trading_allowed",
    "real_orders_possible",
    "holdout_executed",
    "codex_cli_called",
    "ml_signal_validation_executed",
    "predictions_created",
    "labels_created",
    "targets_created",
    "v1_90_execution_attempted",
]


class ConsolidationReadinessSafetyGuard:
    """Checks V1.89 remains a reports-only readiness and approval gate."""

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        for field in EXPECTED_TRUE:
            if payload.get(field) is not True:
                issues.append(f"{field} != true")
        for field in EXPECTED_FALSE:
            if payload.get(field) is not False:
                issues.append(f"{field} != false")
        expected_counts = {
            "v1_84_files_count": 3,
            "v1_87_files_count": 2,
            "v1_84_unexpected_files_count": 0,
            "v1_87_unexpected_files_count": 0,
            "physical_files_created_count": 0,
            "request_retry_count": 0,
        }
        for field, expected in expected_counts.items():
            if payload.get(field) != expected:
                issues.append(f"{field} != {expected}")
        if payload.get("approval_phrase_match") is False and payload.get("human_approval_granted") is True:
            issues.append("human_approval_granted true while approval_phrase_match false")
        if payload.get("human_approval_granted") is True:
            if payload.get("authorized_future_version") != "V1.90":
                issues.append("authorized_future_version != V1.90")
            if payload.get("authorized_future_scope") != AUTHORIZED_FUTURE_SCOPE:
                issues.append("authorized_future_scope mismatch")
        issues.extend(validate_consolidation_design(payload))
        return {"safety_check_passed": not issues, "safety_issues": issues}
