from __future__ import annotations

from typing import Any

import pandas as pd


def _summary(frame: pd.DataFrame) -> dict[str, float]:
    net = pd.to_numeric(frame["realized_net_proxy"], errors="coerce")
    wins = net[net > 0]
    losses = net[net < 0]
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss = float(losses.mean()) if not losses.empty else 0.0
    q = net.quantile([0.01, 0.05, 0.1, 0.5, 0.9]).to_dict()
    return {
        "count": int(len(frame)),
        "mean_net": float(net.mean()),
        "median_net": float(net.median()),
        "win_rate": float((net > 0).mean()),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "payoff_ratio": float(abs(avg_win) / abs(avg_loss)) if avg_loss else None,
        "quantile_01": float(q.get(0.01, 0.0)),
        "quantile_05": float(q.get(0.05, 0.0)),
        "quantile_10": float(q.get(0.1, 0.0)),
        "quantile_50": float(q.get(0.5, 0.0)),
        "quantile_90": float(q.get(0.9, 0.0)),
    }


def run_payoff_degradation(df: pd.DataFrame) -> dict[str, Any]:
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["realized_net_proxy"] = pd.to_numeric(frame["forward_return_12bar"], errors="coerce") - pd.to_numeric(
        frame["cost_proxy"], errors="coerce"
    )
    pre = frame[frame["timestamp"] < pd.Timestamp("2026-01-01")]
    recent = frame[frame["timestamp"] >= pd.Timestamp("2026-01-01")]
    pre_stats = _summary(pre)
    recent_stats = _summary(recent)
    status = (
        "PAYOFF_ASYMMETRY_DEGRADED_2026"
        if recent_stats["avg_loss"] < pre_stats["avg_loss"] and recent_stats["payoff_ratio"] < pre_stats["payoff_ratio"]
        else "PAYOFF_ASYMMETRY_STABLE"
        if abs(recent_stats["payoff_ratio"] - pre_stats["payoff_ratio"]) < 0.1
        else "PAYOFF_DIAGNOSTIC_INCONCLUSIVE"
    )
    return {
        "pre_2026": pre_stats,
        "2026": recent_stats,
        "payoff_asymmetry_delta": {
            "avg_win_delta": recent_stats["avg_win"] - pre_stats["avg_win"],
            "avg_loss_delta": recent_stats["avg_loss"] - pre_stats["avg_loss"],
            "payoff_ratio_delta": (recent_stats["payoff_ratio"] or 0.0) - (pre_stats["payoff_ratio"] or 0.0),
        },
        "payoff_degradation_status": status,
    }
