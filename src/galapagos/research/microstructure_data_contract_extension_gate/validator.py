from __future__ import annotations

from typing import Any

from .approval_gate import AUTHORIZED_SCOPE
from .safety_guard import ExtensionGateSafetyGuard


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors = ExtensionGateSafetyGuard().check(payload)["safety_issues"]
    expected = {
        "approval_gate_only": True,
        "reports_only": True,
        "v1_87_execution_attempted": False,
        "materialization_executed": False,
        "new_materialization_executed": False,
        "data_contract_actual_write_executed": False,
        "data_directory_write_attempted": False,
        "new_data_files_created": False,
        "existing_data_files_modified": False,
        "no_new_data_directory_writes": True,
        "dataset_created": False,
        "network_executed": False,
        "trading_allowed": False,
        "real_orders_possible": False,
        "ml_signal_validation_executed": False,
        "release_ready_for_external_review": True,
        "smoke_test_passed": True,
        "clean_zip_ready_for_external_review": True,
    }
    for field, value in expected.items():
        if payload.get(field) is not value:
            errors.append(f"{field} != {value!r}")
    if payload.get("approval_phrase_match") is False and payload.get("human_approval_granted") is True:
        errors.append("approval granted despite phrase mismatch")
    if payload.get("human_approval_granted") is True:
        if payload.get("authorized_future_version") != "V1.87":
            errors.append("authorized_future_version must be V1.87")
        if payload.get("authorized_future_scope") != AUTHORIZED_SCOPE:
            errors.append("authorized_future_scope mismatch")
    return errors
