from __future__ import annotations

from typing import Any

import pandas as pd


def rebuild_selected_trades(
    df: pd.DataFrame,
    *,
    selected_filter: str = "filter_ev_gt_0",
    source_selected_count: int | None = None,
    source_selected_count_2026: int | None = None,
) -> dict[str, Any]:
    if selected_filter not in df.columns:
        raise ValueError(f"Missing filter column: {selected_filter}")

    selected = df.loc[df[selected_filter]].copy()
    selected["timestamp"] = pd.to_datetime(selected["timestamp"])
    count_total = int(len(selected))
    count_2026 = int((selected["timestamp"] >= pd.Timestamp("2026-01-01")).sum())
    count_match = (
        source_selected_count is None
        or (count_total == int(source_selected_count) and count_2026 == int(source_selected_count_2026 or 0))
    )
    rebuild_status = (
        "EV_DEGRADATION_SELECTED_TRADES_REBUILT"
        if count_match
        else "EV_DEGRADATION_SELECTED_TRADE_REBUILD_MISMATCH"
    )
    return {
        "selected_filter": selected_filter,
        "selected_count_total": count_total,
        "selected_count_2026": count_2026,
        "source_v1_38_4_selected_count": source_selected_count,
        "source_v1_38_4_selected_count_2026": source_selected_count_2026,
        "count_match_v1_38_4": count_match,
        "rebuild_status": rebuild_status,
        "selected_trades": selected,
    }
