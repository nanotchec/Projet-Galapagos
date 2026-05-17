from __future__ import annotations

from typing import Any


class TrainingDatasetPreviewSafetyGuard:
    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        expected_false = [
            "full_training_dataset_created",
            "predictions_created",
            "model_training_executed",
            "ml_signal_validation_executed",
            "backtest_executed",
            "trading_allowed",
            "real_orders_possible",
            "network_executed",
        ]
        for field in expected_false:
            if payload.get(field) is not False:
                issues.append(f"{field} must be false")
        if payload.get("total_new_data_files_created") != 5:
            issues.append("total_new_data_files_created must equal 5")
        if payload.get("total_data_bytes_written", 0) > 75000:
            issues.append("total_data_bytes_written exceeds 75000")
        return {
            "version": "V1.99",
            "safety_check_passed": not issues,
            "safety_issues": issues,
            "real_orders_possible": False,
            "blocking_reason": None if not issues else "; ".join(issues),
        }
