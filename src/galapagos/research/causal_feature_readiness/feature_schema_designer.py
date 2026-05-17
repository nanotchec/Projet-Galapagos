from __future__ import annotations

ALLOWED_THEORETICAL_FEATURE_FAMILIES = [
    "spread_bps",
    "mid_price",
    "bid_ask_imbalance",
    "top_of_book_depth",
    "quote_age_ms",
    "recent_trade_count",
    "recent_trade_volume",
    "realized_volatility_past_window",
    "return_past_window",
    "microprice",
    "order_book_imbalance",
    "liquidity_score",
    "latency_observation_ms",
]


class CausalFeatureSchemaDesigner:
    def design(self) -> dict[str, object]:
        features = [
            {
                "feature_name": family,
                "family": family,
                "dtype": "float",
                "availability_rule": "available_ts <= decision_ts",
                "expression": f"{family}_computed_from_observations_at_or_before_decision_ts",
                "description": "Causal market observation available no later than decision_ts.",
                "source_timestamp_fields": ["event_ts", "available_ts", "decision_ts"],
            }
            for family in ALLOWED_THEORETICAL_FEATURE_FAMILIES
        ]
        return {
            "version": "V1.94",
            "causal_feature_schema_designed": True,
            "feature_schema_design_executed": True,
            "allowed_theoretical_feature_families": ALLOWED_THEORETICAL_FEATURE_FAMILIES,
            "theoretical_features_count": len(features),
            "theoretical_features": features,
            "forbidden_feature_families": [
                "target_like",
                "label_like",
                "prediction_like",
                "future_information",
                "trade_result",
            ],
            "available_ts_policy_defined": True,
            "decision_ts_policy_defined": True,
            "event_ts_policy_defined": True,
            "feature_available_ts_lte_decision_ts_rule_defined": True,
            "no_lookahead_policy_defined": True,
            "future_information_fields_forbidden": True,
            "target_like_fields_forbidden": True,
            "label_like_fields_forbidden": True,
            "prediction_like_fields_forbidden": True,
        }
