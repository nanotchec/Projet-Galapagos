from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_mae_mfe(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze intratrade potential and risk."""
    if df.empty:
        return {}
        
    avg_mae = df["mae_pct"].mean()
    avg_mfe = df["mfe_pct"].mean()
    
    # Winners vs Losers
    winners = df[df["net_pnl_pct"] > 0]
    losers = df[df["net_pnl_pct"] <= 0]
    
    # Potential captured: percentage of losers that had MFE > 0.5% (arbitrary threshold)
    losers_with_potential = len(losers[losers["mfe_pct"] > 0.005]) / len(losers) if not losers.empty else 0
    
    verdict = "NO_INTRATRADE_EDGE"
    if avg_mfe > avg_mae * 1.5:
        verdict = "MFE_EXISTS_BUT_EXITS_FAIL"
    elif avg_mae > 0.02: # 2% MAE is high for 4h signals
        verdict = "MAE_TOO_HIGH_FOR_SIGNAL"
        
    return {
        "mean_mae_pct": avg_mae,
        "mean_mfe_pct": avg_mfe,
        "mfe_mae_ratio": avg_mfe / avg_mae if avg_mae != 0 else float('inf'),
        "losers_with_potential_ratio": losers_with_potential,
        "winners_mfe_pct": winners["mfe_pct"].mean() if not winners.empty else 0,
        "losers_mae_pct": losers["mae_pct"].mean() if not losers.empty else 0,
        "verdict": verdict
    }
