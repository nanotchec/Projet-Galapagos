from __future__ import annotations

from typing import Any

from .safety_guard import ConsolidationReadinessSafetyGuard


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors = ConsolidationReadinessSafetyGuard().check(payload)["safety_issues"]
    expected = {
        "readiness_pack_executed": True,
        "consolidation_design_executed": True,
        "consolidation_executed": False,
        "approval_gate_only": True,
        "reports_only": True,
        "data_contract_actual_write_executed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
        "existing_v1_84_files_modified": False,
        "existing_v1_87_files_modified": False,
        "no_new_data_directory_writes": True,
        "dataset_created": False,
        "research_dataset_updated": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "ml_signal_validation_executed": False,
        "v1_90_execution_attempted": False,
        "data_contract_v2_designed": True,
        "consolidation_plan_created": True,
        "consolidation_plan_reports_only": True,
        "consolidation_plan_theoretical_paths_only": True,
        "future_consolidation_no_network": True,
        "future_consolidation_no_ml": True,
        "future_consolidation_no_trading": True,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "clean_zip_ready_for_external_review": True,
    }
    for field, value in expected.items():
        if payload.get(field) is not value:
            errors.append(f"{field} != {value!r}")
    if payload.get("future_consolidation_max_files", 99) > 3:
        errors.append("future_consolidation_max_files > 3")
    if payload.get("future_consolidation_max_bytes", 99_999) > 25_000:
        errors.append("future_consolidation_max_bytes > 25000")
    return errors
