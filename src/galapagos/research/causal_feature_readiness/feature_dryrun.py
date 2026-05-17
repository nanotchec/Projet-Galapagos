from __future__ import annotations

from typing import Any


class CausalFeatureDryRun:
    def build_preview(self, schema: dict[str, Any], *, max_rows: int = 3) -> dict[str, Any]:
        features = schema["theoretical_features"]
        rows = []
        for index in range(max_rows):
            row = {
                "event_ts": f"2026-01-01T0{index}:00:00Z",
                "available_ts": f"2026-01-01T0{index}:00:01Z",
                "decision_ts": f"2026-01-01T0{index}:00:01Z",
            }
            for feature in features[: min(8, len(features))]:
                row[feature["feature_name"]] = None
            rows.append(row)
        return {
            "version": "V1.94",
            "feature_dry_run_executed": True,
            "feature_dry_run_reports_only": True,
            "feature_dry_run_preview_created": True,
            "feature_dry_run_preview_in_reports_only": True,
            "feature_dry_run_allowed_output_root": "reports/research/causal_feature_dryrun_v1_94/",
            "feature_dry_run_data_write_allowed": False,
            "feature_dry_run_max_preview_rows": 10,
            "feature_dry_run_max_theoretical_features": 20,
            "preview_rows_count": len(rows),
            "theoretical_features_count": len(features),
            "preview_rows": rows,
            "feature_dry_run_no_labels": True,
            "feature_dry_run_no_targets": True,
            "feature_dry_run_no_predictions": True,
            "feature_dry_run_no_ml": True,
            "feature_dry_run_no_trading": True,
        }
