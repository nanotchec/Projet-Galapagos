from __future__ import annotations

from typing import Any


class LabelDryRun:
    def build(self, feature_payloads: dict[str, Any]) -> dict[str, Any]:
        rows_payload = feature_payloads.get("feature_preview_rows.json", {})
        rows = rows_payload.get("rows", []) if isinstance(rows_payload, dict) and isinstance(rows_payload.get("rows"), list) else []
        preview = []
        for index, row in enumerate(rows[:3]):
            preview.append({
                "preview_row_id": f"label_dryrun_row_{index}",
                "source_event_ts": row.get("event_ts") if isinstance(row, dict) else None,
                "source_available_ts": row.get("available_ts") if isinstance(row, dict) else None,
                "source_decision_ts": row.get("decision_ts") if isinstance(row, dict) else None,
                "theoretical_label_horizon": "post_decision_horizon_preview_only",
                "materialized_in_data": False,
                "joined_to_features": False,
                "training_usable_in_v1_96": False,
            })
        return {
            "version": "V1.96",
            "label_dry_run_executed": True,
            "label_dry_run_reports_only": True,
            "label_dry_run_preview_created": True,
            "label_dry_run_preview_in_reports_only": True,
            "label_dry_run_allowed_output_root": "reports/research/label_dryrun_v1_96/",
            "label_dry_run_data_write_allowed": False,
            "label_dry_run_max_preview_rows": 10,
            "label_dry_run_max_theoretical_labels": 5,
            "label_dry_run_preview_rows_count": len(preview),
            "label_dry_run_theoretical_labels_count": 3,
            "label_dry_run_preview_rows": preview,
            "label_dry_run_no_physical_labels": True,
            "label_dry_run_no_predictions": True,
            "label_dry_run_no_ml": True,
            "label_dry_run_no_trading": True,
        }

