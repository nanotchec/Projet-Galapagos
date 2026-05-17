CANONICAL_KEYS = ["timestamp", "model_name", "feature_set", "target", "split_name"]

ALLOWED_SELECTION_COLUMNS = [
    "timestamp",
    "model_name",
    "feature_set",
    "target",
    "split_name",
    "predicted_probability",
    "predicted_label",
    "calibrated_probability",
    "avg_win_past",
    "avg_loss_past",
    "cost_proxy",
    "ev_calibrated_proxy",
    "ev_proxy_ready",
    "warmup_ready"
]

FORBIDDEN_SELECTION_COLUMNS = [
    "actual_target",
    "forward_return_1h",
    "forward_return_4h",
    "forward_return_1d",
    "cost_adjusted_forward_return",
    "future_return",
    "pnl",
    "realized_pnl",
    "exit_reason",
    "mae_realized",
    "mfe_realized",
    "outcome"
]

ALLOWED_OUTCOME_COLUMNS = [
    "timestamp",
    "actual_target",
    "forward_return_4h",
    "pnl",
    "exit_reason",
    "realized_pnl"
]

# V1.36.5 Policy Definitions (Non-Included Features)
POLICIES = {
    "calibration_policy": "walk_forward_calibration_v1_31",
    "ev_proxy_policy": {
        "status": "NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
        "description": "The canonical opportunity universe does not include executable EV/cost features. Future EV-net research must explicitly rebuild calibrated_probability, payoff estimates, cost_proxy and ev_calibrated_proxy before applying any EV-based filter.",
        "ev_filter_reference_note": "filter_ev_gt_cost_buffer is an imported diagnostic reference from V1.35.3 and is not part of canonical_opportunity_rows."
    },
    "cost_policy": {
        "status": "NOT_INCLUDED_IN_CANONICAL_OPPORTUNITY_UNIVERSE",
        "cost_proxy_available": False,
        "cost_column": None,
        "description": "No executable cost proxy is embedded in the canonical opportunity universe. Future EV research must define or rebuild cost_proxy explicitly."
    },
    "leakage_policy": "strict causal separation (selection_frame vs outcome_frame)",
    "fingerprint_policy": "hash of sorted canonical keys head(1000) + definition hash",
    "warmup_policy": "100 periods minimum for payoff/EV estimation without row removal"
}
