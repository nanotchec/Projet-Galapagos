from __future__ import annotations

import pandas as pd


def get_temporal_splits(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Define robust temporal windows for signal validation."""
    if df.empty:
        return {}
        
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    splits = {}
    
    # 1. Full Years
    for year in [2024, 2025, 2026]:
        mask = df["timestamp"].dt.year == year
        if mask.any():
            splits[str(year)] = df[mask]
            
    # 2. Large Windows
    mask_24_25 = (df["timestamp"].dt.year >= 2024) & (df["timestamp"].dt.year <= 2025)
    if mask_24_25.any():
        splits["2024_2025"] = df[mask_24_25]
        
    mask_25_26 = (df["timestamp"].dt.year >= 2025)
    if mask_25_26.any():
        splits["2025_2026_YTD"] = df[mask_25_26]
        
    # 3. Half-Year Splits
    for year in [2024, 2025]:
        mask_h1 = (df["timestamp"].dt.year == year) & (df["timestamp"].dt.month <= 6)
        if mask_h1.any():
            splits[f"{year}_H1"] = df[mask_h1]
            
        mask_h2 = (df["timestamp"].dt.year == year) & (df["timestamp"].dt.month > 6)
        if mask_h2.any():
            splits[f"{year}_H2"] = df[mask_h2]
            
    # 2026 YTD is already covered by the year loop
    
    return splits
