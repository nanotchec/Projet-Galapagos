from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from galapagos.analysis.performance import summarize_profile_performance
from galapagos.journal.sqlite_store import SQLiteStore


def compare_profiles(profile_results: dict[str, dict]) -> dict:
    comparison = {"profiles": profile_results}
    if "galapagos_30m" in profile_results and "galapagos_4h" in profile_results:
        p30 = profile_results["galapagos_30m"]
        p4h = profile_results["galapagos_4h"]
        comparison["trade_count_delta_30m_minus_4h"] = (
            p30.get("trade_count", 0) - p4h.get("trade_count", 0)
        )
        comparison["pnl_delta_30m_minus_4h"] = p30.get("total_pnl", 0.0) - p4h.get(
            "total_pnl", 0.0
        )
    return comparison


def comparison_rows(profile_results: dict[str, dict]) -> list[dict]:
    fields = [
        "profile",
        "cycles_count",
        "trade_count",
        "closed_trade_count",
        "open_position_count",
        "realized_pnl",
        "unrealized_pnl",
        "cash",
        "equity",
        "total_fees",
        "total_slippage",
        "win_rate",
        "risk_rejected_count",
        "no_trade_count",
        "avg_trade_pnl",
        "best_trade",
        "worst_trade",
    ]
    return [
        {field: metrics.get(field, profile if field == "profile" else 0) for field in fields}
        for profile, metrics in profile_results.items()
    ]


def build_profile_comparison(
    store: SQLiteStore,
    *,
    profiles: list[str] | None = None,
) -> dict[str, Any]:
    profiles = profiles or ["galapagos_30m", "galapagos_4h"]
    profile_results = {profile: _profile_metrics(store, profile) for profile in profiles}
    return {"profiles": profile_results, "rows": comparison_rows(profile_results)}


def generate_profile_comparison_report(
    store: SQLiteStore,
    output_dir: str | Path,
    *,
    report_date: date | None = None,
    profiles: list[str] | None = None,
) -> dict[str, Path]:
    report_date = report_date or datetime.now(UTC).date()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    comparison = build_profile_comparison(store, profiles=profiles)
    comparison["date"] = report_date.isoformat()
    md_path = output / f"profile_comparison_{report_date.isoformat()}.md"
    json_path = output / f"profile_comparison_{report_date.isoformat()}.json"
    md_path.write_text(_comparison_markdown(comparison), encoding="utf-8")
    json_path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}


def _profile_metrics(store: SQLiteStore, profile: str) -> dict[str, Any]:
    trades = [
        dict(row)
        for row in store.query(
            "SELECT * FROM paper_trades WHERE profile = ? ORDER BY id",
            (profile,),
        )
    ]
    decisions = [
        dict(row)
        for row in store.query(
            "SELECT * FROM agent_decisions WHERE profile = ? ORDER BY id",
            (profile,),
        )
    ]
    positions = [
        json.loads(row["payload_json"])
        for row in store.query("SELECT payload_json FROM positions")
        if json.loads(row["payload_json"]).get("profile") == profile
    ]
    latest_price = _latest_price(store, profile)
    metrics = summarize_profile_performance(
        profile=profile,
        trades=trades,
        open_positions=positions,
        decisions=decisions,
        current_price=latest_price,
    )
    closed = [trade for trade in trades if trade.get("status") == "CLOSED"]
    pnls = [float(trade.get("pnl") or 0.0) for trade in closed]
    metrics.update(
        {
            "cycles_count": len(decisions),
            "cash": _account_cash(store, profile),
            "equity": _account_cash(store, profile) + metrics.get("unrealized_pnl", 0.0),
            "avg_trade_pnl": sum(pnls) / len(pnls) if pnls else 0.0,
            "best_trade": max(pnls) if pnls else 0.0,
            "worst_trade": min(pnls) if pnls else 0.0,
        }
    )
    return metrics


def _latest_price(store: SQLiteStore, profile: str) -> float | None:
    rows = store.query(
        "SELECT payload_json FROM market_snapshots WHERE profile = ? ORDER BY id DESC LIMIT 1",
        (profile,),
    )
    if not rows:
        return None
    payload = json.loads(rows[0]["payload_json"])
    value = payload.get("market", {}).get("last_close")
    return float(value) if value is not None else None


def _comparison_markdown(comparison: dict[str, Any]) -> str:
    lines = [f"# Comparaison profils Galapagos - {comparison['date']}", ""]
    headers = [
        "profile",
        "cycles_count",
        "trade_count",
        "closed_trade_count",
        "open_position_count",
        "realized_pnl",
        "unrealized_pnl",
        "cash",
        "equity",
        "total_fees",
        "total_slippage",
        "win_rate",
        "risk_rejected_count",
        "no_trade_count",
        "avg_trade_pnl",
        "best_trade",
        "worst_trade",
    ]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in comparison["rows"]:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines)


def _account_cash(store: SQLiteStore, profile: str) -> float:
    rows = store.query("SELECT cash FROM paper_account WHERE profile = ?", (profile,))
    return float(rows[0]["cash"]) if rows else 0.0
