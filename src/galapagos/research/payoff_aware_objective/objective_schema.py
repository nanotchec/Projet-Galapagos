"""Schemas and constants for payoff-aware objective research."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class AnalysisSplit:
    """Chronological walk-forward split used in V1.40."""

    name: str
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


@dataclass(frozen=True)
class ObjectiveCandidateSpec:
    """Definition of a payoff-aware objective candidate."""

    name: str
    description: str
    target_column: str
    feature_columns: tuple[str, ...]
    candidate_type: str
    uses_ev_proxy: bool = False
    uses_probability: bool = False
    uses_downside_weighting: bool = False


LABEL_COLUMNS = (
    "net_return_label",
    "signed_payoff_label",
    "asymmetric_payoff_label",
    "downside_risk_label",
    "ev_gap_label",
)

FORBIDDEN_FEATURE_PREFIXES = (
    "forward_return_",
    "max_favorable_excursion_",
    "max_adverse_excursion_",
    "direction_up_after_cost_",
    "tp_before_sl",
)

FORBIDDEN_FEATURE_COLUMNS = {
    "gross_pnl_pct",
    "net_pnl_pct",
    "mfe_pct",
    "mae_pct",
    "exit_reason",
    "simulation_status",
    "actual_target",
    "cost_adjusted_forward_return",
    "net_return_label",
    "signed_payoff_label",
    "asymmetric_payoff_label",
    "downside_risk_label",
    "ev_gap_label",
    "selected",
    "selected_rebuild",
}

NUMERIC_FEATURE_COLUMNS = (
    "predicted_probability",
    "predicted_probability_calibrated",
    "predicted_label",
    "ev_calibrated_proxy",
    "avg_win_past",
    "avg_loss_past",
    "cost_proxy",
    "combined_alpha_score",
    "combined_alpha_score_no_derivatives",
    "combined_alpha_score_no_macro",
    "ohlcv_only_alpha_score",
    "macro_derivatives_score",
    "ohlcv_momentum_score",
    "ohlcv_breakout_score",
    "volatility_quality_score",
    "macro_regime_score",
    "cost_penalty_score",
    "crowded_trade_penalty",
    "missing_data_penalty",
    "volume_quality_score",
    "derivatives_regime_score",
    "derivatives_crowding_score",
    "derivatives_leverage_score",
    "derivatives_score",
    "funding_rate_zscore_30d",
    "funding_rate_zscore_90d",
    "open_interest_zscore_30d",
    "open_interest_zscore_90d",
    "premium_zscore_30d",
    "taker_imbalance_zscore",
    "long_short_ratio_zscore",
    "price_oi_confirmation",
    "price_oi_divergence",
    "funding_extreme_positive",
    "funding_extreme_negative",
    "open",
    "high",
    "low",
    "close",
    "volume",
)

CATEGORICAL_FEATURE_COLUMNS = (
    "volatility_regime",
    "trend_regime",
    "macro_regime",
    "derivatives_risk_regime",
    "vol_regime_vix",
)

BASE_MODEL_FEATURE_COLUMNS = tuple(
    column
    for column in NUMERIC_FEATURE_COLUMNS
    if column not in {"predicted_probability_calibrated", "ev_calibrated_proxy", "avg_win_past", "avg_loss_past"}
)


def get_causal_feature_columns(columns: Iterable[str]) -> list[str]:
    """Return causal feature columns available in the input frame."""
    available = set(columns)
    result = [
        column
        for column in BASE_MODEL_FEATURE_COLUMNS
        if column in available and column not in FORBIDDEN_FEATURE_COLUMNS
    ]
    return result


def get_categorical_feature_columns(columns: Iterable[str]) -> list[str]:
    """Return categorical columns available in the input frame."""
    available = set(columns)
    return [column for column in CATEGORICAL_FEATURE_COLUMNS if column in available]


def get_label_columns(columns: Iterable[str]) -> list[str]:
    """Return label columns available in the input frame."""
    available = set(columns)
    return [column for column in LABEL_COLUMNS if column in available]


def build_walk_forward_splits(frame: pd.DataFrame) -> list[AnalysisSplit]:
    """Build expanding walk-forward splits ending in the recent 2026 window."""
    if frame.empty or "timestamp" not in frame.columns:
        return []
    ts = pd.to_datetime(frame["timestamp"], utc=True).dropna()
    if ts.empty:
        return []
    min_ts = ts.min().floor("D")
    split_specs = [
        ("2024_H1", pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2024-07-01", tz="UTC")),
        ("2024_H2", pd.Timestamp("2024-07-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")),
        ("2025_H1", pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2025-07-01", tz="UTC")),
        ("2025_H2", pd.Timestamp("2025-07-01", tz="UTC"), pd.Timestamp("2026-01-01", tz="UTC")),
        ("2026_H1", pd.Timestamp("2026-01-01", tz="UTC"), pd.Timestamp("2026-07-01", tz="UTC")),
    ]
    splits: list[AnalysisSplit] = []
    for name, test_start, test_end in split_specs:
        train_start = min_ts
        train_end = test_start
        splits.append(
            AnalysisSplit(
                name=name,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
    return splits


def build_walk_forward_split_integrity(frame: pd.DataFrame) -> dict[str, object]:
    """Return a split integrity report and only the valid walk-forward splits."""
    if frame.empty or "timestamp" not in frame.columns:
        return {
            "split_integrity_status": "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_FAILED",
            "invalid_split_count": 0,
            "invalid_splits": [],
            "skipped_split_count": 0,
            "skipped_splits": [],
            "evaluated_split_count": 0,
            "evaluated_splits": [],
            "train_before_test_enforced": True,
            "no_negative_train_window": True,
            "no_silent_zero_metrics_for_invalid_split": True,
            "all_splits_temporally_valid": False,
            "valid_splits": [],
        }
    ts = pd.to_datetime(frame["timestamp"], utc=True).dropna()
    if ts.empty:
        return {
            "split_integrity_status": "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_FAILED",
            "invalid_split_count": 0,
            "invalid_splits": [],
            "skipped_split_count": 0,
            "skipped_splits": [],
            "evaluated_split_count": 0,
            "evaluated_splits": [],
            "train_before_test_enforced": True,
            "no_negative_train_window": True,
            "no_silent_zero_metrics_for_invalid_split": True,
            "all_splits_temporally_valid": False,
            "valid_splits": [],
        }
    min_ts = ts.min().floor("D")
    split_specs = [
        ("2024_H1", pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2024-07-01", tz="UTC")),
        ("2024_H2", pd.Timestamp("2024-07-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")),
        ("2025_H1", pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2025-07-01", tz="UTC")),
        ("2025_H2", pd.Timestamp("2025-07-01", tz="UTC"), pd.Timestamp("2026-01-01", tz="UTC")),
        ("2026_H1", pd.Timestamp("2026-01-01", tz="UTC"), pd.Timestamp("2026-07-01", tz="UTC")),
    ]

    valid_splits: list[AnalysisSplit] = []
    invalid_splits: list[dict[str, object]] = []
    skipped_splits: list[dict[str, object]] = []
    evaluated_splits: list[dict[str, object]] = []

    for name, test_start, test_end in split_specs:
        train_start = min_ts
        train_end = test_start
        train = frame[(pd.to_datetime(frame["timestamp"], utc=True) >= train_start) & (pd.to_datetime(frame["timestamp"], utc=True) < train_end)]
        test = frame[(pd.to_datetime(frame["timestamp"], utc=True) >= test_start) & (pd.to_datetime(frame["timestamp"], utc=True) < test_end)]
        split_record = {
            "name": name,
            "train_start": train_start.isoformat(),
            "train_end": train_end.isoformat(),
            "test_start": test_start.isoformat(),
            "test_end": test_end.isoformat(),
            "train_count": int(len(train)),
            "test_count": int(len(test)),
        }
        if train_start >= train_end or len(train) == 0:
            skipped_splits.append(
                {
                    **split_record,
                    "skip_reason": "NO_PRIOR_TRAINING_HISTORY",
                    "split_status": "SKIPPED_NO_TRAINING_HISTORY",
                }
            )
            continue
        if not (train_start <= train_end <= test_start < test_end):
            invalid_splits.append(
                {
                    **split_record,
                    "split_status": "INVALID_TEMPORAL_ORDER",
                    "reason": "TEMPORAL_ORDER_VIOLATION",
                }
            )
            continue
        valid_splits.append(
            AnalysisSplit(
                name=name,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        evaluated_splits.append(
            {
                **split_record,
                "split_status": "EVALUATED",
            }
        )

    status = "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_PASSED" if valid_splits and not invalid_splits else "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_FAILED"
    return {
        "split_integrity_status": status,
        "invalid_split_count": len(invalid_splits),
        "invalid_splits": invalid_splits,
        "skipped_split_count": len(skipped_splits),
        "skipped_splits": skipped_splits,
        "evaluated_split_count": len(valid_splits),
        "evaluated_splits": evaluated_splits,
        "train_before_test_enforced": True,
        "no_negative_train_window": True,
        "no_silent_zero_metrics_for_invalid_split": True,
        "all_splits_temporally_valid": not invalid_splits and bool(valid_splits),
        "valid_splits": valid_splits,
    }
