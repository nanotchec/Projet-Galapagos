"""Cost vs gross analysis for payoff-objective failure."""
from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_cost_vs_gross(analysis_frame: pd.DataFrame, score_report: dict[str, Any]) -> dict[str, Any]:
    score_frame = score_report.get("score_frame_2026", pd.DataFrame()).copy()
    if score_frame.empty:
        return {"cost_vs_gross_status": "COST_NOT_PRIMARY_DRIVER", "issues": ["no scored 2026 frame"]}
    score_frame["timestamp"] = pd.to_datetime(score_frame["timestamp"], utc=True)
    top_decile = score_frame.head(max(1, int(round(len(score_frame) * 0.1))))
    gross = pd.to_numeric(top_decile.get("gross_return"), errors="coerce").fillna(0.0)
    net = pd.to_numeric(top_decile.get("net_return"), errors="coerce").fillna(0.0)
    cost = pd.to_numeric(top_decile.get("cost_proxy"), errors="coerce").fillna(0.0)
    gross_mean = float(gross.mean()) if len(gross) else 0.0
    net_mean = float(net.mean()) if len(net) else 0.0
    cost_mean = float(cost.mean()) if len(cost) else 0.0
    if gross_mean <= 0:
        status = "PAYOFF_OBJECTIVE_EDGE_NEGATIVE_BEFORE_COSTS"
    elif gross_mean > 0 and net_mean <= 0:
        status = "COSTS_ERASE_PAYOFF_OBJECTIVE_EDGE"
    else:
        status = "COST_NOT_PRIMARY_DRIVER"
    return {
        "cost_vs_gross_status": status,
        "gross_mean_return_top_decile": gross_mean,
        "cost_proxy_mean_top_decile": cost_mean,
        "net_mean_return_top_decile": net_mean,
        "edge_before_costs": gross_mean,
        "edge_after_costs": net_mean,
        "selected_count_2026": int(len(top_decile)),
        "recent_window_status": score_report.get("recent_window_status"),
    }
