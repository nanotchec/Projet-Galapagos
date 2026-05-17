from __future__ import annotations

import pandas as pd

from galapagos.data.derivatives.coverage import derivatives_data_quality
from galapagos.data.derivatives.features import build_derivatives_features
from galapagos.research.derivatives_signal_quality import (
    analyze_derivatives_signal_quality,
    analyze_filter_hypotheses,
    compare_with_without_derivatives,
)


def test_derivatives_feature_builder_causal_and_regime() -> None:
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
            "metric_value": [0.0001] * 200 + [0.01] * 20,
            "metadata_json": ["{}"] * 220,
        }
    )
    features = build_derivatives_features(records)
    assert "funding_rate_zscore_30d" in features.columns
    assert pd.isna(features["funding_rate_zscore_30d"].iloc[0])
    assert "derivatives_risk_regime" in features.columns


def test_derivatives_signal_quality_and_filters_mock() -> None:
    dataset = pd.DataFrame(
        {
            "forward_return_1bar": [0.01, -0.01, 0.02],
            "forward_return_3bar": [0.01, -0.01, 0.02],
            "forward_return_6bar": [0.02, -0.02, 0.03],
            "forward_return_12bar": [0.02, -0.02, 0.03],
            "max_favorable_excursion_6bar": [0.03, 0.01, 0.04],
            "max_adverse_excursion_6bar": [0.01, 0.03, 0.01],
            "funding_rate_zscore_30d": [2.5, -2.5, 0.0],
            "open_interest_change_3": [0.06, -0.06, 0.0],
            "premium_zscore_30d": [0.0, 0.0, 2.5],
            "taker_imbalance": [0.3, -0.3, 0.0],
            "derivatives_available_count": [3, 3, 2],
            "derivatives_confidence_score": [0.6, 0.6, 0.4],
            "derivatives_risk_regime": ["positive_funding_extreme", "neutral", "neutral"],
        }
    )
    quality = analyze_derivatives_signal_quality(dataset)
    comparison = compare_with_without_derivatives(dataset)
    filters = analyze_filter_hypotheses(dataset)
    assert quality["groups"]["funding_positive_extreme"]["count"] == 1
    assert comparison["with_derivatives_available"]["count"] == 3
    assert "filters" in filters


def test_derivatives_data_quality_empty() -> None:
    payload = derivatives_data_quality("DOES_NOT_EXIST", "4h")
    assert payload["verdict"] == "DERIVATIVES_DATA_TOO_SPARSE"
