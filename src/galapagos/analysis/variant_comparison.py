from __future__ import annotations

import math
from statistics import mean, pstdev
from typing import Any


def summarize_variant_windows(variant_results: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = []
    for variant, windows in variant_results.items():
        pnls = [float(window.get("final_equity_pnl") or 0.0) for window in windows]
        trades = sum(int(window.get("ledger_trade_count") or 0) for window in windows)
        fees = sum(float(window.get("fees") or 0.0) for window in windows)
        slippage = sum(float(window.get("slippage") or 0.0) for window in windows)
        net = sum(pnls)
        rows.append(
            {
                "variant": variant,
                "total_net_pnl": net,
                "mean_window_pnl": mean(pnls) if pnls else 0.0,
                "min_window_pnl": min(pnls) if pnls else 0.0,
                "pnl_std": pstdev(pnls) if len(pnls) > 1 else 0.0,
                "positive_windows_count": sum(1 for value in pnls if value > 0),
                "worst_window": _worst_window(windows),
                "total_trades": trades,
                "total_fees": fees,
                "total_slippage": slippage,
                "total_costs": fees + slippage,
                "cost_per_trade": (fees + slippage) / trades if trades else 0.0,
                "score_prudent": prudent_score(net, pnls, fees, slippage, trades),
            }
        )
    return {
        "rows": rows,
        "best_total_pnl": max(rows, key=lambda row: row["total_net_pnl"], default=None),
        "most_stable": min(rows, key=lambda row: row["pnl_std"], default=None),
        "lowest_costs": min(rows, key=lambda row: row["total_costs"], default=None),
        "verdicts": variant_verdicts(rows),
    }


def summarize_window_report(report: dict[str, Any]) -> dict[str, Any]:
    ledger = report.get("closed_trades_ledger") or []
    return {
        "window": report.get("window_label"),
        "decisions_distribution": report.get("decision_distribution", {}),
        "raw_long_count": (report.get("raw_decision_distribution") or {}).get("LONG", 0),
        "blocked_by_cost_filter": report.get("blocked_by_cost_filter", 0),
        "blocked_by_regime_filter": report.get("blocked_by_regime_filter", 0),
        "close_delayed_count": report.get("agent_close_delayed_count", 0),
        "ledger_trade_count": report.get("ledger_trade_count", 0),
        "gross_pnl": sum(float(trade.get("gross_pnl") or 0.0) for trade in ledger),
        "fees": report.get("fees", 0.0),
        "slippage": report.get("slippage", 0.0),
        "net_pnl": report.get("realized_pnl", 0.0),
        "final_equity_pnl": report.get("final_equity_pnl", 0.0),
        "win_rate": _win_rate(ledger),
        "max_drawdown": _max_drawdown([float(trade.get("net_pnl") or 0.0) for trade in ledger]),
        "average_duration_bars": _avg_duration(ledger),
        "exit_reason_distribution": _exit_reasons(ledger),
        "ledger_pnl_matches_official": report.get("ledger_pnl_matches_official"),
        "cache_hits": (report.get("decision_cache") or {}).get("external_hits", 0),
        "codex_calls": 0,
        "risk_rejects": report.get("risk_rejects", 0),
    }


def prudent_score(
    net_pnl: float,
    pnls: list[float],
    fees: float,
    slippage: float,
    trades: int,
) -> float:
    downside = abs(min(pnls)) if pnls else 0.0
    return net_pnl - downside * 0.5 - (fees + slippage) * 0.05 - trades * 0.25


def variant_verdicts(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["NEED_MORE_CACHED_DECISIONS"]
    baseline = next((row for row in rows if row["variant"] == "long_only_force_close"), None)
    best = max(rows, key=lambda row: row["total_net_pnl"])
    verdicts: list[str] = []
    if baseline and best["variant"] == baseline["variant"]:
        verdicts.append("NO_VARIANT_IMPROVES")
    if "cost_filter" in best["variant"] and best["total_trades"] > 0:
        verdicts.append("COST_FILTER_PROMISING")
    for row in rows:
        if "cost_filter_3x" in row["variant"] and row["total_trades"] == 0:
            verdicts.append("COST_FILTER_TOO_STRICT")
        if "holding" in row["variant"] and row["total_trades"] == (baseline or {}).get(
            "total_trades"
        ):
            verdicts.append("HOLDING_FILTER_NOT_EXERCISED")
        if (
            baseline
            and "regime_filter" in row["variant"]
            and row["total_net_pnl"] > baseline["total_net_pnl"]
        ):
            verdicts.append("REGIME_FILTER_PROMISING")
    if (
        baseline
        and best["variant"] != baseline["variant"]
        and best["positive_windows_count"] >= 2
        and best["min_window_pnl"] >= 0
    ):
        verdicts.append("VARIANT_READY_FOR_HOLDOUT")
    return sorted(set(verdicts or ["NEED_MORE_CACHED_DECISIONS"]))


def _worst_window(windows: list[dict[str, Any]]) -> str | None:
    if not windows:
        return None
    worst = min(windows, key=lambda item: float(item.get("final_equity_pnl") or 0.0))
    return str(worst.get("window"))


def _win_rate(ledger: list[dict[str, Any]]) -> float:
    if not ledger:
        return 0.0
    return sum(1 for trade in ledger if float(trade.get("net_pnl") or 0.0) > 0) / len(ledger)


def _avg_duration(ledger: list[dict[str, Any]]) -> float:
    values = [float(trade.get("duration_bars") or 0.0) for trade in ledger]
    return sum(values) / len(values) if values else 0.0


def _exit_reasons(ledger: list[dict[str, Any]]) -> dict[str, int]:
    output: dict[str, int] = {}
    for trade in ledger:
        reason = str(trade.get("exit_reason") or "unknown")
        output[reason] = output.get(reason, 0) + 1
    return output


def _max_drawdown(pnls: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return 0.0 if math.isclose(drawdown, 0.0) else drawdown
