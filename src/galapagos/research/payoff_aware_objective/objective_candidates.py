"""Objective candidate definitions for payoff-aware research."""
from __future__ import annotations

from typing import Any

from .objective_schema import ObjectiveCandidateSpec, get_causal_feature_columns


def build_objective_candidates(columns: list[str] | tuple[str, ...]) -> dict[str, Any]:
    """Build the exploratory objective candidates and report metadata."""
    causal_features = get_causal_feature_columns(columns)
    ev_features = [
        column
        for column in [
            "predicted_probability_calibrated",
            "ev_calibrated_proxy",
            "avg_win_past",
            "avg_loss_past",
            "cost_proxy",
        ]
        if column in columns
    ]
    base_features = tuple(causal_features)
    regression_features = tuple(dict.fromkeys((*base_features, *ev_features)))
    classifier_features = tuple(dict.fromkeys((*base_features, *ev_features)))
    candidates = [
        ObjectiveCandidateSpec(
            name="probability_only_baseline",
            description="Calibrated probability baseline only.",
            target_column="net_return_label",
            feature_columns=tuple(
                column
                for column in ["predicted_probability_calibrated", "predicted_probability"]
                if column in columns
            ),
            candidate_type="baseline",
            uses_probability=True,
        ),
        ObjectiveCandidateSpec(
            name="expected_net_return_regression",
            description="Ridge regression on net return labels.",
            target_column="net_return_label",
            feature_columns=regression_features,
            candidate_type="regression",
        ),
        ObjectiveCandidateSpec(
            name="asymmetric_loss_weighted_classifier",
            description="Classifier with higher weights on downside errors.",
            target_column="signed_payoff_label",
            feature_columns=classifier_features,
            candidate_type="classifier",
            uses_downside_weighting=True,
        ),
        ObjectiveCandidateSpec(
            name="downside_aware_score",
            description="Regressor trained on downside risk magnitude.",
            target_column="downside_risk_label",
            feature_columns=regression_features,
            candidate_type="downside_regression",
            uses_downside_weighting=True,
        ),
        ObjectiveCandidateSpec(
            name="ev_gap_corrector",
            description="Residual model that corrects EV proxy error.",
            target_column="ev_gap_label",
            feature_columns=tuple(
                dict.fromkeys((*regression_features, "ev_calibrated_proxy"))
            ),
            candidate_type="ev_gap_residual",
            uses_ev_proxy=True,
        ),
        ObjectiveCandidateSpec(
            name="two_head_probability_payoff_model",
            description="Combined probability and payoff objective.",
            target_column="net_return_label",
            feature_columns=regression_features,
            candidate_type="two_head",
            uses_ev_proxy=True,
            uses_probability=True,
            uses_downside_weighting=True,
        ),
    ]
    implemented_candidates = [candidate.name for candidate in candidates]
    return {
        "candidates": candidates,
        "candidates_defined": [candidate.name for candidate in candidates],
        "implemented_candidates": implemented_candidates,
        "skipped_candidates": [],
        "skip_reasons": [],
        "objective_candidate_status": "PAYOFF_OBJECTIVE_CANDIDATES_DEFINED",
    }

