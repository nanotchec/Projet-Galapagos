from __future__ import annotations

from typing import Any


class TrainingDatasetReadinessSafetyGuard:
    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        issues = []
        for field in [
            "physical_feature_label_join_created",
            "training_dataset_created",
            "training_dataset_files_created_in_data",
            "predictions_created",
            "model_training_executed",
            "ml_signal_validation_executed",
            "backtest_executed",
            "data_directory_write_attempted",
            "new_data_files_created",
            "network_executed",
            "trading_allowed",
            "real_orders_possible",
            "v1_99_execution_attempted",
        ]:
            if payload.get(field) is not False:
                issues.append(f"{field} must be false")
        return {
            "version": payload.get("version", "V1.98.2"),
            "safety_check_status": "PASS" if not issues else "FAIL",
            "safety_issues": issues,
            "no_real_trading": payload.get("no_real_trading") is True,
            "no_paper_live": payload.get("no_paper_live") is True,
        }
