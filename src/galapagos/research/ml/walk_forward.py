"""Walk-forward evaluation — strictly chronological, no shuffle."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from galapagos.research.ml.feature_sets import extract_features, get_feature_set
from galapagos.research.ml.metrics import classification_metrics, regression_metrics
from galapagos.research.ml.models import MODEL_REGISTRY, create_model


@dataclass
class WalkForwardWindow:
    """A single train/test split."""
    name: str
    train_start: int
    train_end: int
    test_start: int
    test_end: int

    def validate(self, n_rows: int) -> None:
        if self.train_start >= self.train_end:
            raise ValueError(f"train_start >= train_end in {self.name}")
        if self.test_start >= self.test_end:
            raise ValueError(f"test_start >= test_end in {self.name}")
        if self.train_end > self.test_start:
            raise ValueError(f"Train/test overlap in {self.name}")
        if self.test_end > n_rows:
            raise ValueError(f"test_end ({self.test_end}) > n_rows ({n_rows}) in {self.name}")


def build_default_windows(n_rows: int, embargo_bars: int = 6) -> list[WalkForwardWindow]:
    """Build chronological expanding windows for ~4 years of 4h data."""
    # Approximate: 6 bars/day * 365 days = ~2190 bars/year
    # 2022: 0..2190, 2023: 2190..4380, 2024: 4380..6570, 2025: 6570..8760
    bars_per_year = n_rows // 4 if n_rows > 0 else 2190
    windows = []
    # Window 1: train 2022-2023, test 2024
    w1_train_end = min(2 * bars_per_year, n_rows)
    w1_test_start = w1_train_end + embargo_bars
    w1_test_end = min(3 * bars_per_year, n_rows)
    if w1_test_start < w1_test_end and w1_train_end > 100:
        windows.append(WalkForwardWindow(
            name="validation_2024",
            train_start=0, train_end=w1_train_end,
            test_start=w1_test_start, test_end=w1_test_end,
        ))
    # Window 2: train 2022-2024, test 2025
    w2_train_end = min(3 * bars_per_year, n_rows)
    w2_test_start = w2_train_end + embargo_bars
    w2_test_end = min(4 * bars_per_year, n_rows)
    if w2_test_start < w2_test_end and w2_train_end > 100:
        windows.append(WalkForwardWindow(
            name="validation_2025",
            train_start=0, train_end=w2_train_end,
            test_start=w2_test_start, test_end=w2_test_end,
        ))
    # Window 3: train all except last chunk, test recent
    if n_rows > 4 * bars_per_year + embargo_bars + 50:
        w3_train_end = 4 * bars_per_year
        w3_test_start = w3_train_end + embargo_bars
        w3_test_end = n_rows
        windows.append(WalkForwardWindow(
            name="recent_2026",
            train_start=0, train_end=w3_train_end,
            test_start=w3_test_start, test_end=w3_test_end,
        ))
    return windows


def build_date_based_walk_forward_splits(
    dataset: pd.DataFrame, config: dict[str, Any],
) -> list[WalkForwardWindow]:
    """Build walk-forward windows based on precise dates from config."""
    windows = []
    if "timestamp" not in dataset.columns:
        raise ValueError("Dataset must contain 'timestamp' column for date-based splits.")

    wf_config = config.get("walk_forward", {})
    embargo_bars = wf_config.get("embargo_bars", 6)
    date_windows = wf_config.get("date_windows", [])

    ts = pd.to_datetime(dataset["timestamp"], utc=True)
    n_rows = len(dataset)

    for w_cfg in date_windows:
        name = w_cfg.get("name")
        train_start_dt = pd.to_datetime(w_cfg.get("train_start"), utc=True)
        train_end_dt = pd.to_datetime(w_cfg.get("train_end"), utc=True)
        test_start_dt = pd.to_datetime(w_cfg.get("test_start"), utc=True)
        test_end_dt = pd.to_datetime(w_cfg.get("test_end"), utc=True)

        # Find integer indices
        # Train: [train_start, train_end) - but we use <= for end to be inclusive of the day,
        # or we just use boolean mask. Let's find first/last index.
        train_mask = (ts >= train_start_dt) & (ts <= train_end_dt)
        test_mask = (ts >= test_start_dt) & (ts <= test_end_dt)

        if not train_mask.any() or not test_mask.any():
            continue

        # Get integer bounds using np.flatnonzero to be safe against non-RangeIndex
        import numpy as np
        train_idx = np.flatnonzero(train_mask)
        test_idx = np.flatnonzero(test_mask)
        
        train_start = int(train_idx[0])
        train_end = int(train_idx[-1]) + 1  # exclusive end
        
        # Apply embargo: test must start after train_end + embargo_bars
        # Alternatively, we just take the indices from the date filter,
        # and enforce the embargo by shifting the start if needed.
        test_start = int(test_idx[0])
        if test_start < train_end + embargo_bars:
            test_start = train_end + embargo_bars
            
        test_end = int(test_idx[-1]) + 1 # exclusive end
        
        if test_start < test_end and test_start >= train_end:
            window = WalkForwardWindow(
                name=name,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
            # Validate
            try:
                window.validate(n_rows)
                windows.append(window)
            except ValueError:
                pass

    return windows


def run_walk_forward(
    dataset: pd.DataFrame,
    *,
    target_col: str,
    feature_set_name: str,
    model_name: str,
    windows: list[WalkForwardWindow] | None = None,
    config: dict[str, Any] | None = None,
    embargo_bars: int = 6,
    min_train_rows: int = 200,
    min_test_rows: int = 50,
) -> dict[str, Any]:
    """Run walk-forward evaluation for one target/feature_set/model combination."""
    n = len(dataset)
    if windows is None:
        if config and config.get("walk_forward", {}).get("method") == "date_based":
            windows = build_date_based_walk_forward_splits(dataset, config)
        else:
            windows = build_default_windows(n, embargo_bars)
    feature_cols, feat_report = get_feature_set(dataset, feature_set_name)
    if not feature_cols:
        return {"status": "no_features", "feature_report": feat_report}
    if target_col not in dataset.columns:
        return {"status": "missing_target", "target": target_col}

    model_entry = MODEL_REGISTRY.get(model_name, {})
    model_type = model_entry.get("type", "classification")
    supports_proba = model_entry.get("supports_proba", False)

    window_results = []
    for window in windows:
        window.validate(n)
        train_slice = dataset.iloc[window.train_start:window.train_end]
        test_slice = dataset.iloc[window.test_start:window.test_end]

        # Drop rows with NaN target
        train_mask = train_slice[target_col].notna()
        test_mask = test_slice[target_col].notna()
        x_train = extract_features(train_slice[train_mask], feature_cols).values
        y_train = train_slice.loc[train_mask, target_col].values.astype(float)
        x_test = extract_features(test_slice[test_mask], feature_cols).values
        y_test = test_slice.loc[test_mask, target_col].values.astype(float)

        if len(x_train) < min_train_rows:
            window_results.append({
                "window": window.name, "status": "insufficient_train",
                "train_rows": len(x_train), "min_required": min_train_rows,
            })
            continue
        if len(x_test) < min_test_rows:
            window_results.append({
                "window": window.name, "status": "insufficient_test",
                "test_rows": len(x_test), "min_required": min_test_rows,
            })
            continue

        model = create_model(model_name)
        try:
            model.fit(x_train, y_train)
        except Exception as exc:  # noqa: BLE001
            window_results.append({
                "window": window.name, "status": "fit_error", "error": str(exc),
            })
            continue

        y_pred = model.predict(x_test)
        y_proba = None
        if supports_proba and hasattr(model, "predict_proba"):
            try:
                proba = model.predict_proba(x_test)
                y_proba = proba[:, 1] if proba.shape[1] == 2 else None
            except Exception:  # noqa: BLE001
                pass

        if model_type == "classification":
            metrics = classification_metrics(
                y_test, y_pred, y_proba=y_proba,
            )
        else:
            metrics = regression_metrics(y_test, y_pred)

        window_results.append({
            "window": window.name,
            "status": "completed",
            "train_rows": len(x_train),
            "test_rows": len(x_test),
            "metrics": metrics,
        })

    return {
        "status": "completed",
        "target": target_col,
        "feature_set": feature_set_name,
        "model": model_name,
        "model_type": model_type,
        "feature_report": feat_report,
        "windows": window_results,
    }
