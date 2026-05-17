from __future__ import annotations

import pandas as pd

from galapagos.data.derivatives.coverage import audit_derivatives_coverage_expansion
from galapagos.data.derivatives.features import build_derivatives_features
from galapagos.research.alpha_score_quality import (
    analyze_alpha_score_quality,
    analyze_derivatives_contribution,
)
from galapagos.research.alpha_scoring import build_alpha_scores
from galapagos.research.provider_decision_matrix import build_provider_decision_matrix


def test_derivatives_coverage_expansion_contains_provider_gap() -> None:
    payload = audit_derivatives_coverage_expansion("MISSING", "4h", dry_run=True)
    assert payload["version"] == "V1.14"
    assert payload["metrics"]
    assert "provider_gap" in payload["metrics"][0]
    assert "PAID_PROVIDER_NOT_JUSTIFIED_YET" in payload["verdicts"]


def test_derivatives_score_components_handle_missing_data() -> None:
    records = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=220, freq="4h", tz="UTC").astype(str),
            "available_timestamp": pd.date_range(
                "2024-01-01",
                periods=220,
                freq="4h",
                tz="UTC",
            ).astype(str),
            "source": ["binance"] * 220,
            "symbol": ["BTCUSDT"] * 220,
            "metric_name": ["funding_rate"] * 220,
            "metric_value": [0.0001] * 210 + [0.01] * 10,
            "metadata_json": ["{}"] * 220,
        }
    )
    features = build_derivatives_features(records)
    assert "derivatives_score" in features.columns
    assert "funding_extreme_positive" in features.columns
    assert features["derivatives_missing_count"].max() >= 1


def test_alpha_scoring_normalized_and_quality_buckets() -> None:
    rows = 140
    dataset = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=rows, freq="4h", tz="UTC"),
            "open": range(100, 100 + rows),
            "high": range(102, 102 + rows),
            "low": range(99, 99 + rows),
            "close": range(101, 101 + rows),
            "volume": [10 + (idx % 5) for idx in range(rows)],
            "forward_return_1bar": [0.001] * rows,
            "forward_return_3bar": [0.002] * rows,
            "forward_return_6bar": [0.003] * rows,
            "forward_return_12bar": [0.004] * rows,
            "max_favorable_excursion_6bar": [0.01] * rows,
            "max_adverse_excursion_6bar": [-0.005] * rows,
            "macro_regime": ["risk_on"] * rows,
            "derivatives_score": [0.2] * rows,
            "derivatives_missing_count": [2] * rows,
        }
    )
    scored = build_alpha_scores(dataset)
    assert scored["combined_alpha_score"].between(-1, 1).all()
    quality = analyze_alpha_score_quality(scored)
    assert "bucket_analysis" in quality
    assert quality["rows"] == rows


def test_derivatives_contribution_and_provider_matrix() -> None:
    dataset = pd.DataFrame(
        {
            "combined_alpha_score": [0.1, 0.5, 0.9, -0.5, 0.2],
            "combined_alpha_score_no_derivatives": [0.1, 0.2, 0.3, -0.5, 0.2],
            "ohlcv_only_alpha_score": [0.1, 0.2, 0.3, -0.5, 0.2],
            "derivatives_regime_score": [0.0, 0.4, 0.8, -0.2, 0.1],
            "macro_derivatives_score": [0.0, 0.4, 0.8, -0.2, 0.1],
            "forward_return_1bar": [0, 0.01, 0.02, -0.01, 0],
            "forward_return_3bar": [0, 0.01, 0.02, -0.01, 0],
            "forward_return_6bar": [0, 0.01, 0.02, -0.01, 0],
            "forward_return_12bar": [0, 0.01, 0.02, -0.01, 0],
        }
    )
    contribution = analyze_derivatives_contribution(dataset)
    matrix = build_provider_decision_matrix()
    assert contribution["verdict"] in {
        "DERIVATIVES_CONTRIBUTE_POSITIVELY",
        "DERIVATIVES_CONTRIBUTION_WEAK",
        "DERIVATIVES_CONTRIBUTION_NEGATIVE",
        "DERIVATIVES_TOO_SPARSE_TO_EVALUATE",
    }
    assert any(item["monthly_cost"] == "requires manual check" for item in matrix["providers"])
    assert "DO_NOT_BUY_PROVIDER_YET" in matrix["verdicts"]
