from __future__ import annotations

from typing import Any

import pandas as pd

SCORE_COLUMNS = [
    "ohlcv_momentum_score",
    "ohlcv_breakout_score",
    "volatility_quality_score",
    "macro_regime_score",
    "derivatives_regime_score",
    "cost_penalty_score",
    "crowded_trade_penalty",
    "missing_data_penalty",
    "combined_alpha_score",
    "combined_alpha_score_no_derivatives",
    "combined_alpha_score_no_macro",
    "ohlcv_only_alpha_score",
    "macro_derivatives_score",
]


def build_alpha_scores(dataset: pd.DataFrame) -> pd.DataFrame:
    """Build transparent research-only alpha scores without fitting to PnL."""
    frame = dataset.copy()
    close = _numeric(frame, "close")
    returns = close.pct_change(fill_method=None)
    ma_slow = close.rolling(72, min_periods=12).mean()
    high = _numeric(frame, "high")
    low = _numeric(frame, "low")
    volume = _numeric(frame, "volume")

    frame["ohlcv_momentum_score"] = _clip(((close / ma_slow) - 1.0) * 8)
    rolling_high = high.shift(1).rolling(72, min_periods=12).max()
    rolling_low = low.shift(1).rolling(72, min_periods=12).min()
    breakout_raw = ((close - rolling_low) / (rolling_high - rolling_low).replace(0, pd.NA)) * 2 - 1
    frame["ohlcv_breakout_score"] = _clip(breakout_raw)
    realized_vol = returns.rolling(42, min_periods=12).std()
    median_vol = realized_vol.shift(1).rolling(252, min_periods=42).median()
    frame["volatility_quality_score"] = _clip(1.0 - (realized_vol / median_vol).fillna(1.0))
    frame["macro_regime_score"] = _macro_score(frame)
    frame["derivatives_regime_score"] = _derivatives_score(frame)
    frame["cost_penalty_score"] = _cost_penalty(frame, close)
    frame["crowded_trade_penalty"] = _crowding_penalty(frame)
    frame["missing_data_penalty"] = _missing_penalty(frame)
    frame["volume_quality_score"] = _clip(
        (volume / volume.shift(1).rolling(72, min_periods=12).median()) - 1.0
    )
    frame["combined_alpha_score"] = _clip(
        0.30 * frame["ohlcv_momentum_score"]
        + 0.15 * frame["ohlcv_breakout_score"]
        + 0.15 * frame["volatility_quality_score"]
        + 0.15 * frame["macro_regime_score"]
        + 0.20 * frame["derivatives_regime_score"]
        - 0.15 * frame["cost_penalty_score"]
        - 0.10 * frame["crowded_trade_penalty"]
        - 0.10 * frame["missing_data_penalty"]
    )
    frame["combined_alpha_score_no_derivatives"] = _clip(
        0.35 * frame["ohlcv_momentum_score"]
        + 0.20 * frame["ohlcv_breakout_score"]
        + 0.20 * frame["volatility_quality_score"]
        + 0.15 * frame["macro_regime_score"]
        - 0.15 * frame["cost_penalty_score"]
        - 0.10 * frame["missing_data_penalty"]
    )
    frame["combined_alpha_score_no_macro"] = _clip(
        0.35 * frame["ohlcv_momentum_score"]
        + 0.20 * frame["ohlcv_breakout_score"]
        + 0.15 * frame["volatility_quality_score"]
        + 0.25 * frame["derivatives_regime_score"]
        - 0.15 * frame["cost_penalty_score"]
        - 0.10 * frame["crowded_trade_penalty"]
        - 0.10 * frame["missing_data_penalty"]
    )
    frame["ohlcv_only_alpha_score"] = _clip(
        0.45 * frame["ohlcv_momentum_score"]
        + 0.25 * frame["ohlcv_breakout_score"]
        + 0.20 * frame["volatility_quality_score"]
        - 0.10 * frame["cost_penalty_score"]
    )
    frame["macro_derivatives_score"] = _clip(
        0.45 * frame["macro_regime_score"]
        + 0.45 * frame["derivatives_regime_score"]
        - 0.10 * frame["missing_data_penalty"]
    )
    return frame


def score_report(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "version": "V1.14",
        "rows": int(len(frame)),
        "score_columns": [column for column in SCORE_COLUMNS if column in frame.columns],
        "score_ranges": {
            column: {
                "min": _float(frame[column].min()),
                "max": _float(frame[column].max()),
                "missing_rate": float(frame[column].isna().mean()),
            }
            for column in SCORE_COLUMNS
            if column in frame.columns
        },
        "formula": (
            "0.30 momentum + 0.15 breakout + 0.15 volatility + 0.15 macro "
            "+ 0.20 derivatives - 0.15 costs - 0.10 crowding - 0.10 missing"
        ),
        "research_only": True,
    }


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(pd.NA, index=frame.index, dtype="Float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _clip(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0).clip(-1, 1)


def _macro_score(frame: pd.DataFrame) -> pd.Series:
    if "macro_regime" in frame.columns:
        mapped = frame["macro_regime"].map({"risk_on": 0.5, "neutral": 0.0, "risk_off": -0.5})
        if mapped.notna().any():
            return mapped.fillna(0.0).astype(float)
    candidates = []
    for column in ["equity_market_trend", "liquidity_proxy", "vol_regime_vix"]:
        if column in frame.columns:
            candidates.append(_numeric(frame, column))
    if not candidates:
        return pd.Series(0.0, index=frame.index)
    return _clip(pd.concat(candidates, axis=1).mean(axis=1))


def _derivatives_score(frame: pd.DataFrame) -> pd.Series:
    if "derivatives_score" in frame.columns:
        return _clip(_numeric(frame, "derivatives_score"))
    if "derivatives_regime_score" in frame.columns:
        return _clip(_numeric(frame, "derivatives_regime_score"))
    return pd.Series(0.0, index=frame.index)


def _cost_penalty(frame: pd.DataFrame, close: pd.Series) -> pd.Series:
    if "minimum_expected_move_to_break_even" in frame.columns:
        return _clip(_numeric(frame, "minimum_expected_move_to_break_even") * 100)
    realized_vol = close.pct_change(fill_method=None).rolling(42, min_periods=12).std()
    return _clip((0.003 / realized_vol.replace(0, pd.NA)).fillna(0.5))


def _crowding_penalty(frame: pd.DataFrame) -> pd.Series:
    candidates = []
    for column in ["derivatives_crowding_score", "long_short_crowding"]:
        if column in frame.columns:
            candidates.append(_numeric(frame, column).abs())
    if not candidates:
        return pd.Series(0.0, index=frame.index)
    return _clip(pd.concat(candidates, axis=1).max(axis=1))


def _missing_penalty(frame: pd.DataFrame) -> pd.Series:
    if "derivatives_missing_count" in frame.columns:
        missing = _numeric(frame, "derivatives_missing_count")
        return _clip(missing / max(float(missing.max() or 1), 1.0))
    derivative_cols = [
        column
        for column in frame.columns
        if column.startswith(("funding", "open_interest", "premium"))
    ]
    if not derivative_cols:
        return pd.Series(0.5, index=frame.index)
    return pd.Series(frame[derivative_cols].isna().mean(axis=1), index=frame.index)


def _float(value: Any) -> float | None:
    return None if pd.isna(value) else float(value)
