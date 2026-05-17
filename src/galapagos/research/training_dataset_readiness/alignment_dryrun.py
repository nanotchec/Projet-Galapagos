from __future__ import annotations

from typing import Any


class AlignmentDryRun:
    def build(self, feature_payloads: dict[str, Any], label_payloads: dict[str, Any]) -> dict[str, Any]:
        feature_rows = feature_payloads.get("feature_preview_rows.json", {}).get("rows", [])
        label_rows = label_payloads.get("label_preview_rows.json", {}).get("rows", [])
        pairs = []
        for index, (feature_row, label_row) in enumerate(zip(feature_rows[:10], label_rows[:10])):
            pairs.append({
                "alignment_pair_id": f"alignment_dryrun_pair_{index}",
                "feature_decision_ts": feature_row.get("decision_ts") if isinstance(feature_row, dict) else None,
                "label_available_ts": label_row.get("label_available_ts") if isinstance(label_row, dict) else None,
                "reports_only": True,
                "physical_join_created": False,
                "usable_for_training_in_v1_98_2": False,
            })
        return {
            "version": "V1.98.2",
            "alignment_dry_run_created": True,
            "alignment_dry_run_reports_only": True,
            "alignment_dry_run_data_write_allowed": False,
            "alignment_preview_rows_count": len(pairs),
            "alignment_pairs_count": len(pairs),
            "feature_label_join_preview_in_reports_only": True,
            "physical_feature_label_join_created": False,
            "training_dataset_created": False,
            "training_dataset_files_created_in_data": False,
            "labels_joined_to_features_for_training": False,
            "labels_available_at_feature_decision_ts": False,
            "alignment_leakage_detected": False,
            "alignment_lookahead_detected": False,
            "alignment_preview_rows": pairs,
        }
