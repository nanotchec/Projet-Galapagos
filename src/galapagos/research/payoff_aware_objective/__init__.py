"""Payoff-aware objective research for Galapagos V1.40."""
from __future__ import annotations

from .data_loader import build_analysis_frame, load_inputs
from .diagnostic_verdict import build_research_verdict
from .objective_candidates import build_objective_candidates
from .objective_evaluator import evaluate_objective_candidates, evaluate_score_baseline
from .objective_schema import (
    AnalysisSplit,
    ObjectiveCandidateSpec,
    build_walk_forward_splits,
    build_walk_forward_split_integrity,
    get_causal_feature_columns,
    get_categorical_feature_columns,
    get_label_columns,
)
from .payoff_labeler import build_payoff_labels
from .sample_weighting import (
    build_asymmetric_sample_weights,
    build_downside_sample_weights,
)
from .regime_breakdown import summarize_regime_breakdown
from .temporal_robustness import summarize_temporal_robustness
