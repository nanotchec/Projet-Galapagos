from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galapagos.research.ensemble.candidate_builder import build_reviewer_candidates
from galapagos.research.ensemble.ensemble_scores import compute_agreement, compute_ensemble_scores
from galapagos.research.ensemble.evaluation import evaluate_ensemble_performance


@pytest.fixture
def mock_ensemble_data():
    ts = pd.date_range("2024-01-01", periods=100, freq="4h")
    df = pd.DataFrame({
        "timestamp": ts,
        "model_a_p": [0.6] * 50 + [0.4] * 50,
        "model_b_p": [0.7] * 50 + [0.3] * 50,
        "target": [1] * 60 + [0] * 40,
        "alpha_score_v1_14": np.random.rand(100),
        "macro_regime_score": [0.1] * 100,
        "derivatives_regime_score": [0.2] * 100,
        "forward_return_12bar": [0.01] * 100
    })
    return df


def test_ensemble_aggregation(mock_ensemble_data):
    df = mock_ensemble_data
    model_cols = ["model_a_p", "model_b_p"]
    
    mean_p = compute_ensemble_scores(df, model_cols, method="mean_probability")
    assert mean_p[0] == pytest.approx(0.65)
    assert mean_p[99] == pytest.approx(0.35)
    
    vote = compute_ensemble_scores(df, model_cols, method="majority_vote")
    assert vote[0] == 1.0 # Both > 0.5
    assert vote[99] == 0.0 # Both < 0.5


def test_agreement_score(mock_ensemble_data):
    df = mock_ensemble_data
    model_cols = ["model_a_p", "model_b_p"]
    agreement = compute_agreement(df, model_cols)
    assert agreement[0] == 1.0
    assert agreement[99] == 1.0


def test_evaluation_engine(mock_ensemble_data):
    df = mock_ensemble_data
    perf = evaluate_ensemble_performance(df, "model_a_p", "forward_return_12bar", top_pct=0.1)
    assert perf["count"] == 10
    assert perf["mean_return"] == pytest.approx(0.01)


def test_candidate_builder(mock_ensemble_data, tmp_path):
    df = mock_ensemble_data
    out_path = tmp_path / "candidates.jsonl"
    candidates = build_reviewer_candidates(df, "model_a_p", "model_b_p", out_path, top_n=5)
    assert len(candidates) == 5
    assert Path(out_path).exists()
