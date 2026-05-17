from __future__ import annotations

from typing import Any


def build_anti_leakage_plan() -> dict[str, Any]:
    return {
        "anti_leakage_plan_created": True,
        "causal_timestamp_policy_defined": True,
        "available_ts_policy_defined": True,
        "event_ts_policy_defined": True,
        "decision_ts_policy_defined": True,
        "feature_available_ts_lte_decision_ts_rule_defined": True,
        "no_lookahead_policy_defined": True,
        "provenance_policy_defined": True,
        "manifest_checksum_policy_defined": True,
        "schema_validation_policy_defined": True,
        "future_dataset_rows_preview_limit": 10,
        "anti_leakage_rules": [
            "feature_available_ts must be less than or equal to decision_ts",
            "event_ts must be source-observed and never inferred from outcomes",
            "no lookahead allowed: all features must be finalized at decision_ts",
            "preview rows must not include targets, labels, predictions, EV, MFE or MAE",
        ],
    }
