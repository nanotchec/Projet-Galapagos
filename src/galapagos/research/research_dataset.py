from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.backtest.candidate_selector import (
    candidate_to_dict,
    select_candidate_setups_from_data,
)
from galapagos.backtest.historical_data import find_latest_cached_ohlcv, load_historical_ohlcv
from galapagos.evaluation.window_selector import split_ohlcv_into_windows
from galapagos.research.labeling import add_research_labels
from galapagos.utils.config_loader import load_profile


def load_research_ohlcv(profile_name: str = "4h") -> pd.DataFrame:
    profile = load_profile(profile_name)
    silver_path = (
        Path("data/silver/ohlcv/binance/BTCUSDT")
        / profile["timeframe"]
        / f"BTCUSDT_{profile['timeframe']}_combined.csv"
    )
    if silver_path.exists():
        data = pd.read_csv(silver_path)
        return data.sort_values("timestamp").drop_duplicates("timestamp")
    path = find_latest_cached_ohlcv(profile["symbol"], profile["timeframe"])
    if path is None:
        raise RuntimeError("No cached OHLCV data found for research suite.")
    return load_historical_ohlcv(path).sort_values("timestamp").drop_duplicates("timestamp")


def research_windows(data: pd.DataFrame, labels: list[str]) -> dict[str, pd.DataFrame]:
    min_bars = min(80, max(20, len(data) // 4))
    windows = split_ohlcv_into_windows(data, 4, min_bars_per_window=min_bars)
    base_labels = ["calibration", "validation_1", "validation_2", "holdout"]
    by_label = dict(zip(base_labels, windows, strict=True))
    return {
        label: data.iloc[
            by_label[label].start_index : by_label[label].end_index
        ].reset_index(drop=True)
        for label in labels
    }


def mechanical_signals(profile_name: str, data: pd.DataFrame) -> pd.DataFrame:
    profile = load_profile(profile_name)
    candidates = select_candidate_setups_from_data(
        profile=profile,
        data=data,
        source_policies=["state_aware_breakout", "state_aware_momentum"],
        max_candidates=10_000,
    )
    rows = []
    for candidate in candidates:
        payload = candidate_to_dict(candidate)
        rows.append(
            {
                "index": int(candidate.context_index),
                "timestamp": candidate.decision_timestamp,
                "side": candidate.baseline_decision,
                "group": candidate.baseline_policy,
                "score": candidate.baseline_confidence_hint,
                **payload,
            }
        )
    return pd.DataFrame(rows)


def latest_report(pattern: str) -> Path | None:
    paths = sorted(Path("reports").glob(pattern), key=lambda path: path.stat().st_mtime)
    return paths[-1] if paths else None


def join_asof_causal(
    base_ohlcv: pd.DataFrame,
    features: pd.DataFrame,
    *,
    on: str = "timestamp",
    available_ts_col: str = "available_timestamp",
) -> pd.DataFrame:
    if features.empty:
        return base_ohlcv.copy()
    left = base_ohlcv.copy().sort_values(on)
    right = features.copy().sort_values(available_ts_col)
    left[on] = pd.to_datetime(left[on], utc=True, format="mixed")
    right[available_ts_col] = pd.to_datetime(
        right[available_ts_col],
        utc=True,
        format="mixed",
    )
    joined = pd.merge_asof(
        left,
        right,
        left_on=on,
        right_on=available_ts_col,
        direction="backward",
    )
    validate_no_future_features(joined, on=on, available_ts_col=available_ts_col)
    return joined


def validate_no_future_features(
    dataset: pd.DataFrame,
    *,
    on: str = "timestamp",
    available_ts_col: str = "available_timestamp",
) -> bool:
    if available_ts_col not in dataset.columns:
        return True
    timestamps = pd.to_datetime(dataset[on], utc=True)
    available = pd.to_datetime(dataset[available_ts_col], utc=True)
    future = available.notna() & (available > timestamps)
    if future.any():
        raise ValueError("Future feature leakage detected.")
    return True


def build_research_dataset(
    profile: str,
    start: str | None = None,
    end: str | None = None,
    *,
    include_derivatives: bool = True,
    include_macro: bool = True,
) -> pd.DataFrame:
    data = load_research_ohlcv(profile)
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    if start:
        data = data[data["timestamp"] >= pd.Timestamp(start, tz="UTC")]
    if end:
        data = data[data["timestamp"] <= pd.Timestamp(end, tz="UTC")]
    dataset = add_research_labels(data)
    dataset["derivatives_included"] = False
    dataset["macro_included"] = False
    if include_derivatives:
        dataset["derivatives_feature_status"] = "missing"
        derivatives_path = Path(
            "data/gold/derivatives_features/BTCUSDT/4h/derivatives_features.csv"
        )
        if derivatives_path.exists():
            derivatives_features = pd.read_csv(derivatives_path)
            if not derivatives_features.empty:
                derivative_cols = [
                    col for col in derivatives_features.columns if col != "timestamp"
                ]
                dataset = join_asof_causal(
                    dataset,
                    derivatives_features[derivative_cols],
                    on="timestamp",
                    available_ts_col="available_timestamp",
                )
                if "available_timestamp" in dataset.columns:
                    dataset.rename(
                        columns={"available_timestamp": "derivatives_available_timestamp"},
                        inplace=True,
                    )
                dataset["derivatives_included"] = True
                dataset["derivatives_feature_status"] = "joined_v1_13"
    if include_macro:
        macro_path = Path("data/gold/macro_features/4h/macro_features.csv")
        if macro_path.exists():
            macro_features = pd.read_csv(macro_path)
            if not macro_features.empty:
                feature_cols = [
                    col
                    for col in macro_features.columns
                    if col
                    not in {
                        "timestamp",
                    }
                ]
                joined = join_asof_causal(
                    dataset,
                    macro_features[feature_cols],
                    on="timestamp",
                    available_ts_col="available_timestamp",
                )
                joined["macro_included"] = joined["macro_regime"].fillna("unknown") != "unknown"
                dataset = joined
        if "macro_regime" not in dataset.columns:
            dataset["macro_regime"] = "unknown"
        if "macro_confidence" not in dataset.columns:
            dataset["macro_confidence"] = 0.0
    validate_no_future_features(dataset)
    return dataset.reset_index(drop=True)
