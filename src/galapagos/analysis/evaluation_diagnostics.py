from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from galapagos.analysis.llm_trade_postmortem import analyze_llm_trade_postmortem

WINDOW_FILES = {
    "calibration": "calibration_setup_review.json",
    "validation_1": "validation_1_setup_review.json",
    "validation_2": "validation_2_setup_review.json",
}


def analyze_evaluation_diagnostics(
    *,
    include_calibration: bool = True,
    include_validation: bool = True,
    calibration_dir: str | Path | None = None,
    validation_dir: str | Path | None = None,
    reports_root: str | Path = "reports/evaluation",
) -> dict[str, Any]:
    selected_reports = discover_evaluation_reports(
        include_calibration=include_calibration,
        include_validation=include_validation,
        calibration_dir=calibration_dir,
        validation_dir=validation_dir,
        reports_root=reports_root,
    )
    window_results = []
    all_trades = []
    for window_label, path in selected_reports.items():
        report = json.loads(Path(path).read_text(encoding="utf-8"))
        postmortem = analyze_llm_trade_postmortem(path)
        trades = [dict(trade, window=window_label) for trade in postmortem["trades"]]
        all_trades.extend(trades)
        window_results.append(
            {
                "window": window_label,
                "report_path": str(path),
                "period": report.get("window", {}),
                "candidates_submitted": report.get("candidates_submitted"),
                "decision_distribution": report.get("decision_distribution", {}),
                "setup_quality_distribution": report.get("setup_quality_distribution", {}),
                "parse_success": report.get("final_parse_success_rate"),
                "risk_rejects": report.get("risk_rejects"),
                "ledger_pnl_matches_official": report.get("ledger_pnl_matches_official"),
                "trades": summarize_trades(trades),
                "costs": cost_analysis(trades),
                "side": side_analysis(trades),
                "regime": regime_analysis(trades),
                "setup_quality": setup_quality_analysis(trades),
                "exit_reason": exit_reason_analysis(trades),
            }
        )

    filters = simulate_hypothetical_filters(all_trades)
    verdicts = diagnostics_verdict(
        all_trades=all_trades,
        window_results=window_results,
        filters=filters,
    )
    return {
        "version": "V1.9C",
        "source_reports": {label: str(path) for label, path in selected_reports.items()},
        "windows": window_results,
        "global": {
            "trades": summarize_trades(all_trades),
            "costs": cost_analysis(all_trades),
            "side": side_analysis(all_trades),
            "regime": regime_analysis(all_trades),
            "setup_quality": setup_quality_analysis(all_trades),
            "exit_reason": exit_reason_analysis(all_trades),
        },
        "hypothetical_filters": filters,
        "stability": stability_analysis(window_results),
        "answers": answer_questions(all_trades, window_results, filters),
        "verdict": verdicts,
        "holdout_executed": False,
        "safety": "Le systeme V1.9C ne peut toujours pas passer d'ordre reel.",
    }


def discover_evaluation_reports(
    *,
    include_calibration: bool,
    include_validation: bool,
    calibration_dir: str | Path | None,
    validation_dir: str | Path | None,
    reports_root: str | Path,
) -> dict[str, Path]:
    reports: dict[str, Path] = {}
    root = Path(reports_root)
    if include_calibration:
        cal_dir = Path(calibration_dir) if calibration_dir else _latest_dir_with_file(
            root, WINDOW_FILES["calibration"], require_codex=True
        )
        reports["calibration"] = cal_dir / WINDOW_FILES["calibration"]
    if include_validation:
        val_dir = Path(validation_dir) if validation_dir else _latest_dir_with_file(
            root, WINDOW_FILES["validation_1"], require_codex=True
        )
        reports["validation_1"] = val_dir / WINDOW_FILES["validation_1"]
        reports["validation_2"] = val_dir / WINDOW_FILES["validation_2"]
    missing = [str(path) for path in reports.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing evaluation reports: {missing}")
    return reports


def cost_analysis(trades: list[dict[str, Any]]) -> dict[str, Any]:
    gross = sum(_f(trade.get("gross_pnl")) for trade in trades)
    net = sum(_f(trade.get("net_pnl")) for trade in trades)
    fees = sum(_f(trade.get("fees")) for trade in trades)
    slippage = sum(_f(trade.get("slippage")) for trade in trades)
    total_costs = fees + slippage
    count = len(trades)
    return {
        "trade_count": count,
        "gross_pnl": gross,
        "net_pnl": net,
        "fees": fees,
        "slippage": slippage,
        "total_costs": total_costs,
        "cost_to_gross_ratio": total_costs / abs(gross) if gross else None,
        "cost_per_trade": total_costs / count if count else 0.0,
        "slippage_per_trade": slippage / count if count else 0.0,
        "fees_per_trade": fees / count if count else 0.0,
        "average_gross_pnl_per_trade": gross / count if count else 0.0,
        "average_net_pnl_per_trade": net / count if count else 0.0,
        "positive_gross_destroyed_count": sum(
            1
            for trade in trades
            if _f(trade.get("gross_pnl")) > 0 and _f(trade.get("net_pnl")) <= 0
        ),
        "costs_gt_abs_gross_count": sum(
            1
            for trade in trades
            if _f(trade.get("fees")) + _f(trade.get("slippage"))
            > abs(_f(trade.get("gross_pnl")))
        ),
        "required_average_gross_to_break_even": total_costs / count if count else 0.0,
    }


def side_analysis(trades: list[dict[str, Any]]) -> dict[str, Any]:
    return _bucket(trades, lambda trade: str(trade.get("decision") or "unknown"))


def regime_analysis(trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not any(trade.get("market_regime") for trade in trades):
        return {"status": "regime data insufficient", "buckets": {}}
    return {
        "status": "available",
        "market_regime": _bucket(trades, _market_regime_key),
        "trend_short": _bucket(trades, lambda trade: str(trade.get("trend_short") or "unknown")),
        "trend_long": _bucket(trades, lambda trade: str(trade.get("trend_long") or "unknown")),
        "volatility": _bucket(trades, _volatility_bucket),
    }


def setup_quality_analysis(trades: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "setup_quality": _bucket(
            trades, lambda trade: str(trade.get("setup_quality") or "unknown")
        ),
        "setup_quality_score": _bucket(
            trades,
            lambda trade: _score_bucket(trade.get("setup_quality_score")),
        ),
        "confidence": _bucket(trades, lambda trade: _confidence_bucket(trade.get("confidence"))),
    }


def exit_reason_analysis(trades: list[dict[str, Any]]) -> dict[str, Any]:
    return _bucket(
        trades,
        lambda trade: str(trade.get("close_reason") or "other"),
        include_duration=True,
    )


def summarize_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    net_values = [_f(trade.get("net_pnl")) for trade in trades]
    return {
        "trade_count": len(trades),
        "winning_trades": sum(1 for value in net_values if value > 0),
        "losing_trades": sum(1 for value in net_values if value < 0),
        "win_rate": (
            sum(1 for value in net_values if value > 0) / len(net_values)
            if net_values
            else 0.0
        ),
        "net_pnl": sum(net_values),
        "gross_pnl": sum(_f(trade.get("gross_pnl")) for trade in trades),
        "max_drawdown": _max_drawdown(net_values),
    }


def simulate_hypothetical_filters(trades: list[dict[str, Any]]) -> dict[str, Any]:
    filters = {
        "exclude_short": lambda trade: trade.get("decision") != "SHORT",
        "exclude_setup_quality_acceptable": lambda trade: trade.get("setup_quality")
        != "acceptable",
        "setup_quality_score_gte_0_6": lambda trade: _f(trade.get("setup_quality_score")) >= 0.6,
        "confidence_gte_0_7": lambda trade: _f(trade.get("confidence")) >= 0.7,
        "risk_reward_gte_1_5": lambda trade: _f(trade.get("risk_reward_ratio")) >= 1.5,
        "estimated_cost_impact_lt_25pct": lambda trade: _f(
            trade.get("estimated_cost_impact"), default=999.0
        )
        < 0.25,
        "side_aligned_with_trend_long": _side_aligned_with_trend_long,
        "volatility_reasonable": _volatility_reasonable,
    }
    return {name: _filter_summary(trades, predicate) for name, predicate in filters.items()}


def stability_analysis(window_results: list[dict[str, Any]]) -> dict[str, Any]:
    pnl_values = [_f(window["trades"].get("net_pnl")) for window in window_results]
    return {
        "window_count": len(window_results),
        "net_pnl_values": pnl_values,
        "net_pnl_mean": mean(pnl_values) if pnl_values else 0.0,
        "net_pnl_std": pstdev(pnl_values) if len(pnl_values) > 1 else 0.0,
        "positive_windows": sum(1 for value in pnl_values if value > 0),
        "negative_windows": sum(1 for value in pnl_values if value < 0),
    }


def diagnostics_verdict(
    *,
    all_trades: list[dict[str, Any]],
    window_results: list[dict[str, Any]],
    filters: dict[str, Any],
) -> list[str]:
    verdicts = []
    costs = cost_analysis(all_trades)
    stability = stability_analysis(window_results)
    if costs["total_costs"] > abs(costs["gross_pnl"]):
        verdicts.append("COSTS_DOMINATE")
    if costs["gross_pnl"] <= 0:
        verdicts.append("SIGNAL_WEAK")
    side = side_analysis(all_trades)
    if abs(_f(side.get("LONG", {}).get("net_pnl")) - _f(side.get("SHORT", {}).get("net_pnl"))) > 50:
        verdicts.append("SIDE_BIAS_SUSPECTED")
    if stability["positive_windows"] and stability["negative_windows"]:
        verdicts.append("REGIME_DEPENDENT")
    if not _stable_positive_filters(filters):
        verdicts.append("NO_STABLE_FILTER")
    verdicts.append("NEED_MORE_VALIDATION")
    return verdicts


def answer_questions(
    trades: list[dict[str, Any]],
    window_results: list[dict[str, Any]],
    filters: dict[str, Any],
) -> dict[str, str]:
    costs = cost_analysis(trades)
    side = side_analysis(trades)
    regime = regime_analysis(trades)
    stable_filters = [
        name
        for name, result in filters.items()
        if result["trade_count"] > 0
        and result["net_pnl"] > 0
        and result["improved_windows"] > result["degraded_windows"]
    ]
    return {
        "loss_source": (
            "Les couts dominent le faible edge brut."
            if costs["total_costs"] > abs(costs["gross_pnl"])
            else "Le signal brut semble prioritaire."
        ),
        "costs_flip_positive_gross": (
            "Oui, plusieurs trades et certaines fenetres passent de brut positif a net negatif."
            if costs["positive_gross_destroyed_count"] > 0
            else "Non observe dans les ledgers charges."
        ),
        "long_short_difference": json.dumps(side, ensure_ascii=False),
        "bad_regimes": (
            "Regime data insufficient"
            if regime.get("status") != "available"
            else json.dumps(regime.get("market_regime", {}), ensure_ascii=False)
        ),
        "stable_filters": ", ".join(stable_filters) if stable_filters else "Aucun filtre stable.",
        "robust_hypothesis_for_v1_10": (
            "Tester sans SHORT et avec controles de couts en validation supplementaire."
            if "exclude_short" in stable_filters
            else "Aucune hypothese suffisamment robuste; renforcer les baselines par fenetre."
        ),
        "holdout_should_remain_locked": "Oui.",
    }


def _latest_dir_with_file(root: Path, filename: str, *, require_codex: bool) -> Path:
    candidates = [path.parent for path in root.glob(f"*/{filename}")]
    if require_codex:
        candidates = [
            path
            for path in candidates
            if _report_has_codex_payload(path / filename)
        ]
    if not candidates:
        raise FileNotFoundError(f"No evaluation report found for {filename}")
    return max(candidates, key=lambda path: (path / filename).stat().st_mtime)


def _report_has_codex_payload(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return False
    return bool(payload.get("closed_trades_ledger") is not None and payload.get("reviews"))


def _bucket(
    trades: list[dict[str, Any]],
    key_func,
    *,
    include_duration: bool = False,
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        buckets[str(key_func(trade))].append(trade)
    result = {}
    for key, bucket_trades in buckets.items():
        costs = cost_analysis(bucket_trades)
        summary = summarize_trades(bucket_trades)
        result[key] = {
            **summary,
            "fees": costs["fees"],
            "slippage": costs["slippage"],
            "total_costs": costs["total_costs"],
            "average_net_pnl": costs["average_net_pnl_per_trade"],
        }
        if include_duration:
            durations = [_f(trade.get("duration_hours")) for trade in bucket_trades]
            result[key]["average_duration_hours"] = (
                sum(durations) / len(durations) if durations else 0.0
            )
    return result


def _filter_summary(trades: list[dict[str, Any]], predicate) -> dict[str, Any]:
    selected = [trade for trade in trades if predicate(trade)]
    by_window = {}
    for window in sorted({str(trade.get("window")) for trade in trades}):
        original = [trade for trade in trades if str(trade.get("window")) == window]
        filtered = [trade for trade in selected if str(trade.get("window")) == window]
        by_window[window] = {
            "original_net_pnl": sum(_f(trade.get("net_pnl")) for trade in original),
            "filtered_net_pnl": sum(_f(trade.get("net_pnl")) for trade in filtered),
            "trades_remaining": len(filtered),
        }
        by_window[window]["delta"] = (
            by_window[window]["filtered_net_pnl"] - by_window[window]["original_net_pnl"]
        )
    summary = summarize_trades(selected)
    return {
        **summary,
        "gross_pnl": sum(_f(trade.get("gross_pnl")) for trade in selected),
        "total_costs": sum(_f(trade.get("fees")) + _f(trade.get("slippage")) for trade in selected),
        "by_window": by_window,
        "improved_windows": sum(1 for item in by_window.values() if item["delta"] > 0),
        "degraded_windows": sum(1 for item in by_window.values() if item["delta"] < 0),
    }


def _stable_positive_filters(filters: dict[str, Any]) -> bool:
    return any(
        result["trade_count"] > 0
        and result["net_pnl"] > 0
        and result["improved_windows"] >= result["degraded_windows"]
        for result in filters.values()
    )


def _market_regime_key(trade: dict[str, Any]) -> str:
    regime = trade.get("market_regime")
    if isinstance(regime, dict):
        return str(regime.get("trend") or "unknown")
    return str(regime or "unknown")


def _volatility_bucket(trade: dict[str, Any]) -> str:
    value = trade.get("volatility")
    if isinstance(value, str):
        return value
    if value is None:
        return "unknown"
    numeric = _f(value)
    if numeric < 0.006:
        return "low"
    if numeric <= 0.018:
        return "normal"
    return "high"


def _score_bucket(value: Any) -> str:
    numeric = _f(value)
    if numeric < 0.4:
        return "<0.4"
    if numeric < 0.6:
        return "0.4-0.6"
    if numeric <= 0.8:
        return "0.6-0.8"
    return ">0.8"


def _confidence_bucket(value: Any) -> str:
    numeric = _f(value)
    if numeric < 0.5:
        return "<0.5"
    if numeric <= 0.7:
        return "0.5-0.7"
    return ">0.7"


def _side_aligned_with_trend_long(trade: dict[str, Any]) -> bool:
    side = str(trade.get("decision") or "")
    trend = str(trade.get("trend_long") or "")
    return (side == "LONG" and trend == "up") or (side == "SHORT" and trend == "down")


def _volatility_reasonable(trade: dict[str, Any]) -> bool:
    value = trade.get("volatility")
    if isinstance(value, str):
        return value in {"normal", "low"}
    numeric = _f(value, default=-1.0)
    return 0.004 <= numeric <= 0.018


def _max_drawdown(pnl_values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for pnl in pnl_values:
        equity += pnl
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return drawdown


def _f(value: Any, *, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
