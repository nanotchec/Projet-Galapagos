from __future__ import annotations

from typing import Any


class FeaturePreviewSafetyGuard:
    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        expected_false = [
            "full_feature_dataset_created",
            "labels_created",
            "targets_created",
            "predictions_created",
            "model_training_executed",
            "ml_signal_validation_executed",
            "network_executed",
            "trading_allowed",
            "real_orders_possible",
            "unapproved_data_write_detected",
            "existing_seed_files_modified",
        ]
        issues = [field for field in expected_false if payload.get(field) is not False]
        return {"version": "V1.95", "safety_check_passed": not issues, "safety_issues": issues}
