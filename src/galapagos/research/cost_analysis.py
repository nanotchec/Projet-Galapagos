from __future__ import annotations


def analyze_costs(trades: list[dict]) -> dict:
    gross = sum(float(trade.get("gross_pnl") or 0.0) for trade in trades)
    fees = sum(float(trade.get("fees") or 0.0) for trade in trades)
    slippage = sum(float(trade.get("slippage") or 0.0) for trade in trades)
    net = sum(float(trade.get("net_pnl") or trade.get("pnl") or 0.0) for trade in trades)
    total_costs = fees + slippage
    count = len(trades)
    positive_gross_destroyed = sum(
        1
        for trade in trades
        if float(trade.get("gross_pnl") or 0.0) > 0
        and float(trade.get("net_pnl") or trade.get("pnl") or 0.0) <= 0
    )
    costs_gt_abs_gross = sum(
        1
        for trade in trades
        if (float(trade.get("fees") or 0.0) + float(trade.get("slippage") or 0.0))
        > abs(float(trade.get("gross_pnl") or 0.0))
    )
    return {
        "trade_count": count,
        "gross_pnl": gross,
        "fees": fees,
        "slippage": slippage,
        "net_pnl": net,
        "total_costs": total_costs,
        "costs_to_abs_gross_ratio": total_costs / abs(gross) if gross else None,
        "average_cost_per_trade": total_costs / count if count else 0.0,
        "break_even_move_required": total_costs / count if count else 0.0,
        "net_edge_after_cost": net / count if count else 0.0,
        "positive_gross_destroyed_count": positive_gross_destroyed,
        "costs_gt_abs_gross_count": costs_gt_abs_gross,
        "costs_dominate": total_costs > abs(gross) if gross else total_costs > 0,
    }


def cost_verdict(analysis: dict) -> list[str]:
    verdicts = []
    if analysis.get("costs_dominate"):
        verdicts.append("COSTS_DOMINATE")
    if (analysis.get("net_pnl") or 0.0) < (analysis.get("gross_pnl") or 0.0):
        verdicts.append("EDGE_REDUCED_BY_COSTS")
    if (analysis.get("positive_gross_destroyed_count") or 0) > 0:
        verdicts.append("POSITIVE_GROSS_TRADES_DESTROYED")
    return verdicts or ["COSTS_NOT_DOMINANT_ON_SAMPLE"]

