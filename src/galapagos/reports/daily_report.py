from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from galapagos.analysis.performance import summarize_profile_performance
from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.utils.time_utils import utc_now_iso


def generate_daily_report(result: dict[str, Any], output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    profile = result["decision"]["profile"]
    stamp = utc_now_iso().replace(":", "").replace("+", "Z")
    md_path = output / f"{profile}_{stamp}.md"
    json_path = output / f"{profile}_{stamp}.json"
    performance = result.get("performance", {})
    content = f"""# Rapport quotidien Galapagos - {profile}

## Resume
- Decision finale: {result["risk"]["final_action"]}
- Decision agent: {result["decision"]["decision"]}
- Execution: {result["execution"].get("action")}
- Provider LLM: {result["llm_provider_status"]["provider"]}
- Mode donnees: {result["snapshot"]["data_quality"].get("data_mode")}
- Positions ouvertes: {performance.get("open_position_count", 0)}
- Trades fermes: {performance.get("closed_trade_count", 0)}

## Raisons risk engine
{chr(10).join(f"- {reason}" for reason in result["risk"]["reasons"]) or "- Aucune"}

## Positions et performance
- Realized PnL: {performance.get("realized_pnl", 0.0)}
- Unrealized PnL: {performance.get("unrealized_pnl", 0.0)}
- Fees: {performance.get("total_fees", 0.0)}
- Slippage: {performance.get("total_slippage", 0.0)}
- Risk rejected decisions: {performance.get("risk_rejected_count", 0)}
- No trade decisions: {performance.get("no_trade_count", 0)}
- Open positions count: {performance.get("open_position_count", 0)}

## Sorties de position du cycle
{_format_exit_events(result.get("position_exit_events", []))}

## Synthese marche
- Actif: {result["snapshot"]["asset"]}
- Timeframe: {result["snapshot"]["timeframe"]}
- Derniere cloture: {result["snapshot"]["market"].get("last_close")}
- Regime: {result["snapshot"]["indicators"].get("market_regime")}
"""
    md_path.write_text(content, encoding="utf-8")
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}


def _format_exit_events(events: list[dict[str, Any]]) -> str:
    if not events:
        return "- Aucune"
    lines = []
    for event in events:
        trade = event.get("trade", {})
        lines.append(
            f"- {trade.get('side')} {trade.get('asset')} ferme: "
            f"{trade.get('close_reason')} / PnL {trade.get('pnl')}"
        )
    return "\n".join(lines)


def generate_daily_summary(
    store: SQLiteStore,
    output_dir: str | Path,
    *,
    report_date: date | None = None,
    profiles: list[str] | None = None,
) -> dict[str, Path]:
    report_date = report_date or datetime.now(UTC).date()
    profiles = profiles or ["galapagos_30m", "galapagos_4h"]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    start = f"{report_date.isoformat()}T00:00:00"
    end = f"{report_date.isoformat()}T23:59:59"

    summary = {
        "date": report_date.isoformat(),
        "profiles": {
            profile: _profile_daily_metrics(store, profile, start, end) for profile in profiles
        },
        "system_errors": _system_errors(store, start, end),
    }
    md_path = output / f"galapagos_daily_summary_{report_date.isoformat()}.md"
    json_path = output / f"galapagos_daily_summary_{report_date.isoformat()}.json"
    md_path.write_text(_daily_summary_markdown(summary), encoding="utf-8")
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}


def _profile_daily_metrics(
    store: SQLiteStore,
    profile: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    decisions = [
        dict(row)
        for row in store.query(
            """
            SELECT * FROM agent_decisions
            WHERE profile = ? AND timestamp_utc BETWEEN ? AND ?
            ORDER BY id
            """,
            (profile, start, end),
        )
    ]
    trades = [
        dict(row)
        for row in store.query(
            "SELECT * FROM paper_trades WHERE profile = ? ORDER BY id",
            (profile,),
        )
    ]
    positions = [
        json.loads(row["payload_json"])
        for row in store.query("SELECT payload_json FROM positions")
        if json.loads(row["payload_json"]).get("profile") == profile
    ]
    latest_snapshot = store.query(
        """
        SELECT payload_json FROM market_snapshots
        WHERE profile = ? ORDER BY id DESC LIMIT 1
        """,
        (profile,),
    )
    latest_price = None
    derivatives_status: dict[str, Any] = {}
    if latest_snapshot:
        snapshot = json.loads(latest_snapshot[0]["payload_json"])
        latest_price = snapshot.get("market", {}).get("last_close")
        derivatives_status = _derivatives_availability(snapshot.get("derivatives", {}))
    metrics = summarize_profile_performance(
        profile=profile,
        trades=trades,
        open_positions=positions,
        decisions=decisions,
        current_price=latest_price,
    )
    counts = {"LONG": 0, "SHORT": 0, "CLOSE": 0, "HOLD": 0, "NO_TRADE": 0}
    for decision in decisions:
        parsed = _loads(decision.get("parsed_decision"))
        name = parsed.get("decision")
        if name in counts:
            counts[name] += 1
    metrics.update(
        {
            "cycles_count": len(decisions),
            "decision_counts": counts,
            "cash": _account_cash(store, profile),
            "equity": (_account_cash(store, profile) or 0.0) + metrics.get("unrealized_pnl", 0.0),
            "max_drawdown": _max_drawdown(store, profile),
            "derivatives_availability": derivatives_status,
        }
    )
    return metrics


def _daily_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [f"# Rapport quotidien global Galapagos - {summary['date']}", ""]
    for profile, metrics in summary["profiles"].items():
        lines.extend(
            [
                f"## {profile}",
                f"- Cycles executes: {metrics.get('cycles_count', 0)}",
                f"- Decisions: {metrics.get('decision_counts', {})}",
                f"- Decisions refusees risk engine: {metrics.get('risk_rejected_count', 0)}",
                f"- Positions ouvertes: {metrics.get('open_position_count', 0)}",
                f"- Cash: {metrics.get('cash', 0.0)}",
                f"- Equity: {metrics.get('equity', 0.0)}",
                f"- Trades fermes: {metrics.get('closed_trade_count', 0)}",
                f"- Realized PnL: {metrics.get('realized_pnl', 0.0)}",
                f"- Unrealized PnL: {metrics.get('unrealized_pnl', 0.0)}",
                f"- Fees: {metrics.get('total_fees', 0.0)}",
                f"- Slippage: {metrics.get('total_slippage', 0.0)}",
                f"- Win rate: {metrics.get('win_rate', 0.0)}",
                f"- Max drawdown approx.: {metrics.get('max_drawdown', 0.0)}",
                f"- Disponibilite derivees: {metrics.get('derivatives_availability', {})}",
                "",
            ]
        )
    lines.extend(["## Erreurs systeme", _format_system_errors(summary["system_errors"])])
    return "\n".join(lines)


def _format_system_errors(errors: list[dict[str, Any]]) -> str:
    if not errors:
        return "- Aucune"
    return "\n".join(f"- {error['timestamp_utc']} {error['message']}" for error in errors)


def _system_errors(store: SQLiteStore, start: str, end: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in store.query(
            """
            SELECT timestamp_utc, level, message, payload_json FROM system_events
            WHERE level = 'ERROR' AND timestamp_utc BETWEEN ? AND ?
            ORDER BY id DESC
            """,
            (start, end),
        )
    ]


def _derivatives_availability(derivatives: dict[str, Any]) -> dict[str, str]:
    return {
        key: value.get("status", "missing")
        for key, value in derivatives.items()
        if isinstance(value, dict)
    }


def _max_drawdown(store: SQLiteStore, profile: str) -> float:
    rows = store.query(
        "SELECT payload_json FROM performance_snapshots WHERE profile = ? ORDER BY id",
        (profile,),
    )
    peak: float | None = None
    max_drawdown = 0.0
    for row in rows:
        payload = json.loads(row["payload_json"])
        equity = float(payload.get("equity") or 0.0)
        peak = equity if peak is None else max(peak, equity)
        if peak:
            max_drawdown = min(max_drawdown, (equity - peak) / peak)
    return max_drawdown


def _account_cash(store: SQLiteStore, profile: str) -> float:
    rows = store.query("SELECT cash FROM paper_account WHERE profile = ?", (profile,))
    return float(rows[0]["cash"]) if rows else 0.0


def _loads(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
