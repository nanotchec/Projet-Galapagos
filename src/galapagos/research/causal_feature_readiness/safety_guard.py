from __future__ import annotations

from typing import Any


class CausalFeatureReadinessSafetyGuard:
    EXPECTED_FALSE = [
        "feature_generation_executed",
        "physical_features_created",
        "feature_files_created_in_data",
        "labels_created",
        "targets_created",
        "predictions_created",
        "model_training_executed",
        "ml_signal_validation_executed",
        "data_directory_write_attempted",
        "new_data_files_created",
        "dataset_created",
        "network_executed",
        "trading_allowed",
        "real_orders_possible",
        "v1_95_execution_attempted",
    ]

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues = [field for field in self.EXPECTED_FALSE if payload.get(field) is not False]
        return {
            "version": "V1.94",
            "safety_check_passed": not issues,
            "safety_issues": issues,
            "no_data_write": payload.get("data_directory_write_attempted") is False,
            "no_network": payload.get("network_executed") is False,
            "no_trading": payload.get("real_orders_possible") is False,
            "no_ml": payload.get("ml_signal_validation_executed") is False,
        }
