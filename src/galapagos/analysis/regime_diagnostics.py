from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.backtest.historical_data import find_latest_cached_ohlcv, load_historical_ohlcv
from galapagos.evaluation.window_selector import split_ohlcv_into_windows

WINDOW_FILES = {
    "calibration": "calibration_setup_review.json",
    "validation_1": "validation_1_setup_review.json",
    "validation_2": "validation_2_setup_review.json",
}


def analyze_regime_and_holding(
    *,
    reports_root: str | Path = "reports/evaluation",
    symbol: str = "BTC/USD",
    timeframe: str = "4h",
) -> dict[str, Any]:
    data_path = _find_longest_cached_ohlcv(symbol, timeframe)
    if data_path is None:
        raise FileNotFoundError("No cached 4h OHLCV data found.")
    data = load_historical_ohlcv(data_path).sort_values("timestamp").drop_duplicates("timestamp")
    windows = split_ohlcv_into_windows(data, n_windows=4, min_bars_per_window=80)
    labels = ["calibration", "validation_1", "validation_2", "holdout"]
    window_by_label = {label: window for label, window in zip(labels, windows, strict=True)}

    reports = discover_source_reports(reports_root)
    trades = load_ledger_trades(reports)
    window_regimes = {
        label: classify_window_regime(
            data.iloc[window.start_index : window.end_index].reset_index(drop=True),
            label=label,
            window=window.to_dict(),
        )
        for label, window in window_by_label.items()
    }
    enriched_trades = enrich_trades_with_window_regime(trades, window_regimes)
    side_regime = side_performance_by_regime(enriched_trades)
    holding = holding_time_analysis(enriched_trades)
    hypotheses = holding_hypotheses(enriched_trades)
    verdicts = diagnostics_verdict(window_regimes, side_regime, holding, enriched_trades)
    return {
        "version": "V1.10.2",
        "data_path": str(data_path),
        "source_reports": {key: str(value) for key, value in reports.items()},
        "window_regimes": window_regimes,
        "side_performance_by_regime": side_regime,
        "holding_time": holding,
        "holding_hypotheses": hypotheses,
        "answers": answer_questions(window_regimes, side_regime, holding),
        "verdicts": verdicts,
        "holdout_executed": False,
        "recommendations": [
            "Tester un filtre side-aware conditionne au regime, sans toucher au holdout.",
            "Ajouter une politique de sortie holding-aware en backtest offline avant GPT.",
            "Renforcer le filtre cost-aware avant tout nouveau run GPT.",
            "Concevoir un module macro separe avec statut unknown explicite.",
            "Ne pas introduire de levier tant qu'un edge net sans levier n'est pas valide.",
        ],
        "safety": "Le système V1.10.2 ne peut toujours pas passer d’ordre réel.",
    }


def classify_window_regime(
    data: pd.DataFrame,
    *,
    label: str = "window",
    window: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if data.empty:
        raise ValueError("Cannot classify an empty OHLCV window.")
    close = pd.to_numeric(data["close"], errors="coerce")
    returns = close.pct_change().dropna()
    start_price = float(close.iloc[0])
    end_price = float(close.iloc[-1])
    return_pct = (end_price - start_price) / start_price if start_price else 0.0
    cumulative = close / start_price if start_price else close * 0
    drawdowns = cumulative / cumulative.cummax() - 1
    max_drawdown = float(drawdowns.min()) if len(drawdowns) else 0.0
    realized_volatility = float(returns.std(ddof=0) * (6 * 365) ** 0.5) if len(returns) else 0.0
    trend_slope = float((end_price - start_price) / max(len(close) - 1, 1))
    ma_short = close.rolling(20, min_periods=1).mean()
    ma_long = close.rolling(60, min_periods=1).mean()
    pct_above_short = float((close > ma_short).mean())
    pct_above_long = float((close > ma_long).mean())
    label_value = _regime_label(
        return_pct=return_pct,
        realized_volatility=realized_volatility,
        pct_above_long=pct_above_long,
        max_drawdown=max_drawdown,
    )
    return {
        "label": label,
        "window": window or {},
        "start_price": start_price,
        "end_price": end_price,
        "return_pct": return_pct,
        "max_drawdown": max_drawdown,
        "realized_volatility": realized_volatility,
        "trend_slope": trend_slope,
        "percent_candles_above_ma_short": pct_above_short,
        "percent_candles_above_ma_long": pct_above_long,
        "regime_label": label_value,
    }


def side_performance_by_regime(trades: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        side = str(trade.get("side") or trade.get("decision") or "unknown")
        regime = str(trade.get("window_regime_label") or _trade_regime(trade))
        vol = _volatility_bucket(trade.get("volatility_entry") or trade.get("volatility"))
        buckets[f"{side}_in_{regime}"].append(trade)
        if vol == "high_volatility":
            buckets[f"{side}_in_high_volatility"].append(trade)
    return {key: _trade_summary(value, include_exit=True) for key, value in buckets.items()}


def holding_time_analysis(trades: list[dict[str, Any]]) -> dict[str, Any]:
    winners = [trade for trade in trades if _f(trade.get("net_pnl")) > 0]
    losers = [trade for trade in trades if _f(trade.get("net_pnl")) < 0]
    return {
        "average_winner_duration_hours": _avg_duration(winners),
        "average_loser_duration_hours": _avg_duration(losers),
        "duration_buckets": _duration_buckets(trades),
        "exit_reason": _exit_reason_buckets(trades),
    }


def holding_hypotheses(trades: list[dict[str, Any]]) -> dict[str, Any]:
    stopped = [trade for trade in trades if trade.get("exit_reason") == "stop_loss"]
    take_profit = [trade for trade in trades if trade.get("exit_reason") == "take_profit"]
    agent_close = [trade for trade in trades if trade.get("exit_reason") == "agent_close"]
    max_duration = [trade for trade in trades if trade.get("exit_reason") == "max_duration"]
    return {
        "double_max_duration_candidates": {
            "count": len(max_duration),
            "note": (
                "Approximation: ces trades auraient explicitement atteint max_duration. "
                "Aucune simulation fiable de bougies futures n'est appliquee ici."
            ),
        },
        "ignore_agent_close_candidates": {
            "count": len(agent_close),
            "note": "Approximation: aucun changement n'est applique sans rejouer les bougies.",
        },
        "take_profit_farther_candidates": {
            "count": len(take_profit),
            "average_take_profit_duration_hours": _avg_duration(take_profit),
            "note": (
                "Si les gagnants sortent tres vite, un TP plus eloigne pourrait etre teste "
                "offline. Ce n'est pas une preuve."
            ),
        },
        "wider_stop_recovery_candidates": {
            "count": len(stopped),
            "average_stop_duration_hours": _avg_duration(stopped),
            "note": (
                "Les stop_loss courts indiquent un besoin de diagnostic, pas que des stops "
                "plus larges auraient gagne."
            ),
        },
    }


def discover_source_reports(reports_root: str | Path) -> dict[str, Path]:
    root = Path(reports_root)
    reports: dict[str, Path] = {}
    # Prefer original V1.9 calibration/validation for LONG vs SHORT regime diagnosis.
    calibration = _latest_matching_report(root, "btc_4h_anti_overfit_v1_9_*", "calibration")
    validation_1 = _latest_matching_report(root, "btc_4h_anti_overfit_v1_9_*", "validation_1")
    validation_2 = _latest_matching_report(root, "btc_4h_anti_overfit_v1_9_*", "validation_2")
    if calibration:
        reports["calibration"] = calibration
    if validation_1:
        reports["validation_1"] = validation_1
    if validation_2:
        reports["validation_2"] = validation_2
    if len(reports) < 3:
        for label, filename in WINDOW_FILES.items():
            path = _latest_any_report(root, filename)
            if path:
                reports[label] = path
    missing = [label for label in WINDOW_FILES if label not in reports]
    if missing:
        raise FileNotFoundError(f"Missing source reports for windows: {missing}")
    return reports


def load_ledger_trades(reports: dict[str, Path]) -> list[dict[str, Any]]:
    trades = []
    for window, path in reports.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("closed_trades_ledger", []):
            trade = dict(item)
            trade["window"] = window
            trade["source_report"] = str(path)
            trades.append(trade)
    return trades


def enrich_trades_with_window_regime(
    trades: list[dict[str, Any]],
    window_regimes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched = []
    for trade in trades:
        payload = dict(trade)
        regime = window_regimes.get(str(payload.get("window")), {})
        payload["window_regime_label"] = regime.get("regime_label")
        payload["window_return_pct"] = regime.get("return_pct")
        enriched.append(payload)
    return enriched


def answer_questions(
    window_regimes: dict[str, dict[str, Any]],
    side_regime: dict[str, Any],
    holding: dict[str, Any],
) -> dict[str, str]:
    return {
        "calibration_regime": _window_answer(window_regimes, "calibration"),
        "validation_1_regime": _window_answer(window_regimes, "validation_1"),
        "validation_2_regime": _window_answer(window_regimes, "validation_2"),
        "holdout_metadata_regime": _window_answer(window_regimes, "holdout"),
        "shorts_fail_in_uptrend": (
            "Probable si les buckets SHORT_in_uptrend sont negatifs."
            if _f(side_regime.get("SHORT_in_uptrend", {}).get("net_pnl")) < 0
            else "Non confirme par les ledgers charges."
        ),
        "holding_time_issue": (
            "A investiguer: les perdants et gagnants ont des durees courtes."
            if holding["average_loser_duration_hours"] <= holding["average_winner_duration_hours"]
            else "Les perdants durent deja plus longtemps que les gagnants."
        ),
    }


def diagnostics_verdict(
    window_regimes: dict[str, dict[str, Any]],
    side_regime: dict[str, Any],
    holding: dict[str, Any],
    trades: list[dict[str, Any]] | None = None,
) -> list[str]:
    verdicts = []
    if sum(1 for item in window_regimes.values() if item["regime_label"] == "uptrend") >= 2:
        verdicts.append("RECENT_UPTREND_BIAS_CONFIRMED")
    if _f(side_regime.get("SHORT_in_uptrend", {}).get("net_pnl")) < 0:
        verdicts.append("SHORT_UNDERPERFORMS_IN_UPTREND")
    if holding["exit_reason"].get("stop_loss", {}).get("trade_count", 0) > 0:
        verdicts.append("HOLDING_TIME_NEEDS_REVIEW")
    source_trades = trades or []
    costs = sum(_f(item.get("fees")) + _f(item.get("slippage")) for item in source_trades)
    gross = sum(_f(item.get("gross_pnl")) for item in source_trades)
    if costs > abs(gross):
        verdicts.append("COSTS_STILL_DOMINATE")
    verdicts.append("MACRO_CONTEXT_RECOMMENDED")
    verdicts.append("LEVERAGE_NOT_READY")
    return verdicts


def _regime_label(
    *,
    return_pct: float,
    realized_volatility: float,
    pct_above_long: float,
    max_drawdown: float,
) -> str:
    if realized_volatility > 0.9 and abs(return_pct) < 0.08:
        return "high_volatility"
    if return_pct > 0.05 and pct_above_long > 0.55:
        return "uptrend"
    if return_pct < -0.05 and pct_above_long < 0.45:
        return "downtrend"
    if abs(return_pct) <= 0.05 and abs(max_drawdown) < 0.12:
        return "range"
    return "mixed"


def _latest_matching_report(root: Path, pattern: str, label: str) -> Path | None:
    filename = WINDOW_FILES[label]
    candidates = [
        path / filename
        for path in root.glob(pattern)
        if (path / filename).exists() and _has_ledger(path / filename)
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def _latest_any_report(root: Path, filename: str) -> Path | None:
    candidates = [path for path in root.glob(f"*/{filename}") if _has_ledger(path)]
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def _has_ledger(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return False
    return isinstance(payload.get("closed_trades_ledger"), list)


def _find_longest_cached_ohlcv(symbol: str, timeframe: str) -> Path | None:
    latest = find_latest_cached_ohlcv(symbol, timeframe)
    if latest is None:
        return None
    candidates = [*latest.parent.glob("*.parquet"), *latest.parent.glob("*.csv")]
    best_path = latest
    best_rows = -1
    for candidate in candidates:
        try:
            rows = len(load_historical_ohlcv(candidate))
        except Exception:  # noqa: BLE001
            continue
        if rows > best_rows:
            best_path = candidate
            best_rows = rows
    return best_path


def _trade_summary(trades: list[dict[str, Any]], *, include_exit: bool = False) -> dict[str, Any]:
    net = [_f(trade.get("net_pnl")) for trade in trades]
    gross = sum(_f(trade.get("gross_pnl")) for trade in trades)
    result = {
        "trade_count": len(trades),
        "gross_pnl": gross,
        "net_pnl": sum(net),
        "win_rate": sum(1 for value in net if value > 0) / len(net) if net else 0.0,
        "fees": sum(_f(trade.get("fees")) for trade in trades),
        "slippage": sum(_f(trade.get("slippage")) for trade in trades),
        "average_duration_hours": _avg_duration(trades),
    }
    if include_exit:
        result["exit_reason_distribution"] = {
            reason: len(bucket)
            for reason, bucket in _group(trades, lambda item: item.get("exit_reason", "other"))
            .items()
        }
    return result


def _duration_buckets(trades: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        label: _trade_summary(bucket)
        for label, bucket in _group(trades, lambda trade: _duration_bucket(trade)).items()
    }


def _exit_reason_buckets(trades: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        label: _trade_summary(bucket)
        for label, bucket in _group(trades, lambda trade: trade.get("exit_reason", "other"))
        .items()
    }


def _duration_bucket(trade: dict[str, Any]) -> str:
    bars = trade.get("duration_bars")
    if bars is None:
        bars = _f(trade.get("duration_hours")) / 4
    bars = _f(bars)
    if bars < 1:
        return "<1 bougie"
    if bars <= 2:
        return "1-2 bougies"
    if bars <= 6:
        return "3-6 bougies"
    return ">6 bougies"


def _group(trades: list[dict[str, Any]], key_func) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        groups[str(key_func(trade))].append(trade)
    return groups


def _avg_duration(trades: list[dict[str, Any]]) -> float:
    durations = [_f(trade.get("duration_hours")) for trade in trades]
    return sum(durations) / len(durations) if durations else 0.0


def _trade_regime(trade: dict[str, Any]) -> str:
    regime = trade.get("market_regime_entry") or trade.get("market_regime")
    if isinstance(regime, dict):
        return str(regime.get("trend") or "unknown")
    return str(regime or "unknown")


def _volatility_bucket(value: Any) -> str:
    numeric = _f(value, default=-1.0)
    if numeric < 0:
        return "unknown"
    if numeric > 0.018:
        return "high_volatility"
    if numeric < 0.006:
        return "low_volatility"
    return "normal_volatility"


def _window_answer(window_regimes: dict[str, dict[str, Any]], label: str) -> str:
    item = window_regimes.get(label, {})
    return (
        f"{item.get('regime_label')} avec return_pct={_f(item.get('return_pct')):.2%}"
        if item
        else "indisponible"
    )


def _f(value: Any, *, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
