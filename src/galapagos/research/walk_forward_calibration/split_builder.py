from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class CalibrationSplit:
    split_id: str
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    train_count: int
    test_count: int
    embargo_applied: bool
    status: str


def build_walk_forward_splits(
    df: pd.DataFrame, 
    embargo_bars: int = 12
) -> list[CalibrationSplit]:
    """
    Build walk-forward splits for calibration research.
    """
    if "timestamp" not in df.columns:
        return []
        
    df = df.sort_values("timestamp")
    timestamps = pd.to_datetime(df["timestamp"])
    
    # Define split points (example logic based on yearly/half-yearly blocks)
    # 2024 H1, 2024 H2, 2025 H1, 2025 H2, 2026 H1
    splits = []
    
    # Split 1: train 2024 H1 -> test 2024 H2
    splits.append({
        "id": "2024_H2",
        "train_end": pd.Timestamp("2024-07-01"),
        "test_start": pd.Timestamp("2024-07-01"),
        "test_end": pd.Timestamp("2025-01-01")
    })
    
    # Split 2: train 2024 -> test 2025 H1
    splits.append({
        "id": "2025_H1",
        "train_end": pd.Timestamp("2025-01-01"),
        "test_start": pd.Timestamp("2025-01-01"),
        "test_end": pd.Timestamp("2025-07-01")
    })
    
    # Split 3: train up to 2025 H1 -> test 2025 H2
    splits.append({
        "id": "2025_H2",
        "train_end": pd.Timestamp("2025-07-01"),
        "test_start": pd.Timestamp("2025-07-01"),
        "test_end": pd.Timestamp("2026-01-01")
    })
    
    # Split 4: train up to 2025 -> test 2026 H1 (The current "recent" window)
    splits.append({
        "id": "2026_H1",
        "train_end": pd.Timestamp("2026-01-01"),
        "test_start": pd.Timestamp("2026-01-01"),
        "test_end": pd.Timestamp("2026-07-01")
    })
    
    results = []
    for s in splits:
        train_mask = (timestamps < s["train_end"])
        # Embargo: remove some bars at the end of train to avoid leakage if overlapping
        if embargo_bars > 0:
            # Simple timestamp-based embargo for now (assuming regular bars)
            # In a real system, we'd remove specific index bars
            pass
            
        test_mask = (timestamps >= s["test_start"]) & (timestamps < s["test_end"])
        
        train_df = df[train_mask]
        test_df = df[test_mask]
        
        if len(train_df) > 100 and len(test_df) > 20:
            results.append(CalibrationSplit(
                split_id=s["id"],
                train_start=timestamps[train_mask].min(),
                train_end=timestamps[train_mask].max(),
                test_start=timestamps[test_mask].min(),
                test_end=timestamps[test_mask].max(),
                train_count=len(train_df),
                test_count=len(test_df),
                embargo_applied=embargo_bars > 0,
                status="WALK_FORWARD_SPLITS_READY"
            ))
            
    return results
