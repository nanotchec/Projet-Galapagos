from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.backtest.historical_data import (
    find_latest_cached_ohlcv,
    load_historical_ohlcv,
)

FEE_RATE = 0.001
SLIPPAGE_BPS = 5.0


def analyze_llm_trade_postmortem(report_path: str | Path) -> dict[str, Any]:
    report_path = Path(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    ledger = report.get("closed_trades_ledger") or []
    source_of_truth = "closed_trades_ledger" if ledger else "reconstructed_from_reviews"
    if ledger:
        trades = [_trade_from_ledger(item) for item in ledger]
    else:
        data = _load_data(report)
        trades = [
            _trade_postmortem(review, data)
            for review in report.get("reviews", [])
            if review.get("decision") in {"LONG", "SHORT"}
        ]
    filter_results = simulate_filters(trades)
    causes = _loss_causes(trades)
    ledger_pnl = sum(float(item["net_pnl"]) for item in trades)
    official_pnl = float(report.get("realized_pnl") or 0.0)
    return {
        "version": "V1.8C.9",
        "source_report": str(report_path),
        "source_version": report.get("version"),
        "source_of_truth": source_of_truth,
        "trades_analyzed": len(trades),
        "source_report_realized_pnl": float(report.get("realized_pnl") or 0.0),
        "source_report_unrealized_pnl": float(report.get("unrealized_pnl") or 0.0),
        "source_report_fees": float(report.get("fees") or 0.0),
        "source_report_slippage": float(report.get("slippage") or 0.0),
        "total_net_pnl": ledger_pnl,
        "total_gross_pnl_before_fees": sum(float(item["gross_pnl"]) for item in trades),
        "total_fees": sum(float(item["fees"]) for item in trades),
        "total_slippage": sum(float(item["slippage"]) for item in trades),
        "winning_trades": sum(1 for item in trades if item["net_pnl"] > 0),
        "losing_trades": sum(1 for item in trades if item["net_pnl"] < 0),
        "would_win_without_costs": sum(1 for item in trades if item["gross_pnl"] > 0),
        "loss_causes": causes,
        "filter_results": filter_results,
        "ledger_pnl_matches_official": abs(ledger_pnl - official_pnl) <= 1e-6,
        "ledger_pnl_delta": ledger_pnl - official_pnl,
        "aggregations": _aggregations(trades),
        "trades": trades,
        "prompt_hardening_recommendations": _recommendations(causes, filter_results),
        "limitations": [
            (
                "Le ledger officiel est utilise si present; sinon le post-mortem retombe sur "
                "une reconstruction explicite."
            ),
            "Echantillon limite a 20 candidats.",
            "Les donnees derivees etaient indisponibles dans les contextes analyses.",
            "Ce rapport explique la mecanique; il ne prouve pas une profitabilite.",
        ],
        "safety": "Le systeme V1.8C.9 ne peut toujours pas passer d'ordre reel.",
    }


def _trade_from_ledger(item: dict[str, Any]) -> dict[str, Any]:
    gross = float(item.get("gross_pnl") or 0.0)
    fees = float(item.get("fees") or 0.0)
    slippage = float(item.get("slippage") or 0.0)
    net = float(item.get("net_pnl") or 0.0)
    expected_move = _expected_move_from_ledger(item)
    cost_fraction = 2 * FEE_RATE + 2 * SLIPPAGE_BPS / 10_000
    setup_quality = str(item.get("setup_quality") or "")
    trade = {
        "trade_id": item.get("trade_id"),
        "candidate_id": item.get("candidate_id_entry"),
        "timestamp": item.get("entry_timestamp"),
        "decision": item.get("side"),
        "setup_quality": setup_quality,
        "setup_quality_score": item.get("setup_quality_score"),
        "confidence": float(item.get("confidence") or 0.0),
        "risk_fraction": float(item.get("risk_fraction") or 0.0),
        "strategy": item.get("strategy"),
        "reasoning_summary": (item.get("entry_decision") or {}).get("reasoning_summary"),
        "candidate_baseline_source": (item.get("candidate_setup") or {}).get("baseline_policy"),
        "entry_price": item.get("entry_price"),
        "stop_loss": (item.get("entry_decision") or {}).get("stop_loss"),
        "take_profit": (item.get("entry_decision") or {}).get("take_profit"),
        "risk_reward_ratio": item.get("risk_reward_initial"),
        "close_reason": item.get("exit_reason"),
        "exit_price": item.get("exit_price"),
        "gross_pnl": gross,
        "fees": fees,
        "slippage": slippage,
        "net_pnl": net,
        "would_have_won_without_fees_slippage": gross > 0,
        "duration_bars": item.get("duration_bars"),
        "duration_hours": item.get("duration_hours"),
        "market_regime": item.get("market_regime_entry"),
        "trend_short": item.get("trend_short_entry"),
        "trend_long": item.get("trend_long_entry"),
        "volatility": item.get("volatility_entry"),
        "derivatives_available": _available_derivatives_from_ledger(item),
        "derivatives_unavailable": _unavailable_derivatives_from_ledger(item),
        "estimated_cost_impact": cost_fraction / expected_move if expected_move > 0 else 999.0,
    }
    trade["probable_loss_causes"] = _trade_loss_causes(
        net_pnl=net,
        gross_pnl=gross,
        risk_reward=trade["risk_reward_ratio"],
        setup_quality=setup_quality,
        derivatives_unavailable=trade["derivatives_unavailable"],
        close_reason=str(item.get("exit_reason") or ""),
        estimated_cost_impact=trade["estimated_cost_impact"],
        review=item,
    )
    return trade


def estimate_risk_reward(
    entry: float | None,
    stop: float | None,
    take: float | None,
) -> float | None:
    if not entry or not stop or not take:
        return None
    risk = abs(entry - stop)
    reward = abs(take - entry)
    if risk <= 0:
        return None
    return reward / risk


def simulate_filters(trades: list[dict[str, Any]]) -> dict[str, Any]:
    filters = {
        "all_gpt_validated": lambda trade: True,
        "setup_quality_good_or_excellent": lambda trade: trade["setup_quality"]
        in {"good", "excellent"},
        "setup_quality_score_gte_0_6": lambda trade: (trade["setup_quality_score"] or 0.0)
        >= 0.6,
        "confidence_gte_0_7": lambda trade: trade["confidence"] >= 0.7,
        "risk_reward_gte_1_5": lambda trade: (trade["risk_reward_ratio"] or 0.0) >= 1.5,
        "estimated_cost_impact_lt_25pct": lambda trade: trade["estimated_cost_impact"] < 0.25,
    }
    return {name: _filter_summary(trades, predicate) for name, predicate in filters.items()}


def _load_data(report: dict[str, Any]) -> pd.DataFrame | None:
    reviews = report.get("reviews", [])
    if not reviews:
        return None
    first = reviews[0].get("candidate", {})
    data_path = find_latest_cached_ohlcv(
        first.get("asset", "BTC/USD"),
        first.get("timeframe", "4h"),
    )
    if data_path is None:
        return None
    return load_historical_ohlcv(data_path).reset_index(drop=True)


def _expected_move_from_ledger(item: dict[str, Any]) -> float:
    entry = item.get("entry_price")
    take = (item.get("entry_decision") or {}).get("take_profit")
    if not entry or not take:
        return 0.0
    return abs(float(take) - float(entry)) / float(entry)


def _available_derivatives_from_ledger(item: dict[str, Any]) -> list[str]:
    availability = item.get("derivatives_availability_entry") or {}
    return [key for key, status in availability.items() if status == "available"]


def _unavailable_derivatives_from_ledger(item: dict[str, Any]) -> list[str]:
    availability = item.get("derivatives_availability_entry") or {}
    return [key for key, status in availability.items() if status != "available"]


def _trade_postmortem(review: dict[str, Any], data: pd.DataFrame | None) -> dict[str, Any]:
    raw = _safe_json(review.get("raw_response"))
    candidate = review.get("candidate", {})
    position = (review.get("execution_event") or {}).get("position", {})
    side = review.get("decision")
    entry = float(position.get("entry_price") or raw.get("reference_entry_price") or 0.0)
    stop = _optional_float(raw.get("stop_loss") or position.get("stop_loss"))
    take = _optional_float(raw.get("take_profit") or position.get("take_profit"))
    size = float(position.get("size") or 0.0)
    risk_reward = estimate_risk_reward(entry, stop, take)
    outcome = _estimate_outcome(candidate, side, entry, stop, take, size, data)
    fees = float(position.get("entry_fee") or 0.0) + outcome["exit_fee"]
    slippage = float(position.get("entry_slippage") or 0.0) + outcome["exit_slippage"]
    net_pnl = outcome["gross_pnl"] - fees
    expected_move = abs(float(take or entry) - entry) / entry if entry else 0.0
    estimated_cost_fraction = 2 * FEE_RATE + 2 * SLIPPAGE_BPS / 10_000
    return {
        "candidate_id": candidate.get("candidate_id"),
        "timestamp": candidate.get("decision_timestamp"),
        "decision": side,
        "setup_quality": raw.get("setup_quality"),
        "setup_quality_score": raw.get("setup_quality_score"),
        "confidence": float(raw.get("confidence") or 0.0),
        "risk_fraction": float(raw.get("risk_fraction") or 0.0),
        "strategy": raw.get("strategy"),
        "reasoning_summary": raw.get("reasoning_summary"),
        "candidate_baseline_source": candidate.get("baseline_policy"),
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit": take,
        "risk_reward_ratio": risk_reward,
        "close_reason": outcome["close_reason"],
        "exit_price": outcome["exit_price"],
        "gross_pnl": outcome["gross_pnl"],
        "fees": fees,
        "slippage": slippage,
        "net_pnl": net_pnl,
        "would_have_won_without_fees_slippage": outcome["gross_pnl"] > 0,
        "duration_bars": outcome["duration_bars"],
        "market_regime": _market_regime(review),
        "trend_short": _trend_from_review(review, "trend_short"),
        "trend_long": _trend_from_review(review, "trend_long"),
        "volatility": _volatility_from_review(review),
        "derivatives_available": _derivatives_available(review),
        "derivatives_unavailable": _derivatives_unavailable(review),
        "estimated_cost_impact": (
            estimated_cost_fraction / expected_move if expected_move > 0 else 999.0
        ),
        "probable_loss_causes": _trade_loss_causes(
            net_pnl=net_pnl,
            gross_pnl=outcome["gross_pnl"],
            risk_reward=risk_reward,
            setup_quality=str(raw.get("setup_quality") or ""),
            derivatives_unavailable=_derivatives_unavailable(review),
            close_reason=outcome["close_reason"],
            estimated_cost_impact=estimated_cost_fraction / expected_move
            if expected_move > 0
            else 999.0,
            review=review,
        ),
    }


def _estimate_outcome(
    candidate: dict[str, Any],
    side: str,
    entry: float,
    stop: float | None,
    take: float | None,
    size: float,
    data: pd.DataFrame | None,
    lookahead_bars: int = 12,
) -> dict[str, Any]:
    if data is None or not len(data):
        return _outcome_from_price(entry, entry, side, size, "data_unavailable", 0)
    start = int(candidate.get("context_index") or 0) + 1
    end = min(start + lookahead_bars, len(data))
    exit_price = float(data["close"].iloc[min(end, len(data)) - 1])
    close_reason = "lookahead_end"
    duration = max(0, end - start)
    for offset, (_, candle) in enumerate(data.iloc[start:end].iterrows(), start=1):
        high = float(candle["high"])
        low = float(candle["low"])
        if side == "LONG":
            if stop is not None and low <= stop:
                return _outcome_from_price(entry, stop, side, size, "stop_loss", offset)
            if take is not None and high >= take:
                return _outcome_from_price(entry, take, side, size, "take_profit", offset)
        if side == "SHORT":
            if stop is not None and high >= stop:
                return _outcome_from_price(entry, stop, side, size, "stop_loss", offset)
            if take is not None and low <= take:
                return _outcome_from_price(entry, take, side, size, "take_profit", offset)
    return _outcome_from_price(entry, exit_price, side, size, close_reason, duration)


def _outcome_from_price(
    entry: float,
    exit_price: float,
    side: str,
    size: float,
    reason: str,
    duration_bars: int,
) -> dict[str, Any]:
    adjusted_exit, exit_slippage = _apply_slippage(exit_price, side, "exit")
    gross = (adjusted_exit - entry) * size if side == "LONG" else (entry - adjusted_exit) * size
    return {
        "exit_price": adjusted_exit,
        "exit_slippage": exit_slippage,
        "exit_fee": abs(adjusted_exit * size) * FEE_RATE,
        "gross_pnl": gross,
        "close_reason": reason,
        "duration_bars": duration_bars,
    }


def _apply_slippage(price: float, side: str, action: str) -> tuple[float, float]:
    rate = SLIPPAGE_BPS / 10_000
    direction = 1 if action == "entry" else -1
    if side == "SHORT":
        direction *= -1
    adjusted = price * (1 + direction * rate)
    return adjusted, abs(adjusted - price)


def _trade_loss_causes(
    *,
    net_pnl: float,
    gross_pnl: float,
    risk_reward: float | None,
    setup_quality: str,
    derivatives_unavailable: list[str],
    close_reason: str,
    estimated_cost_impact: float,
    review: dict[str, Any],
) -> list[str]:
    causes = []
    if net_pnl < 0 and gross_pnl > 0:
        causes.append("frais/slippage detruisent le trade")
    if estimated_cost_impact >= 0.25:
        causes.append("frais/slippage eleves vs potentiel")
    if close_reason == "stop_loss":
        causes.append("stop trop serre")
    if risk_reward is not None and risk_reward < 1.5:
        causes.append("mauvais ratio risk/reward")
    if setup_quality == "acceptable":
        causes.append("setup_quality seulement acceptable")
    if derivatives_unavailable:
        causes.append("donnees derivees indisponibles")
    text = json.dumps(review, ensure_ascii=False).lower()
    if "contradict" in text or "contradictoire" in text:
        causes.append("tendance contradictoire")
    if "volatil" in text and ("unfavorable" in text or "defavorable" in text):
        causes.append("volatilite defavorable")
    if "baseline" in text or "mechanical" in text or "mecanique" in text:
        causes.append("baseline setup faible")
    return causes or ["autre"]


def _loss_causes(trades: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"trade_count": 0, "total_pnl": 0.0, "examples": []}
    )
    for trade in trades:
        if trade["net_pnl"] >= 0:
            continue
        for cause in trade["probable_loss_causes"]:
            buckets[cause]["trade_count"] += 1
            buckets[cause]["total_pnl"] += trade["net_pnl"]
            if len(buckets[cause]["examples"]) < 3:
                buckets[cause]["examples"].append(trade["candidate_id"])
    return dict(buckets)


def _aggregations(trades: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "pnl_by_setup_quality": _pnl_bucket(trades, "setup_quality"),
        "pnl_by_side": _pnl_bucket(trades, "decision"),
        "pnl_by_exit_reason": _pnl_bucket(trades, "close_reason"),
        "pnl_by_strategy": _pnl_bucket(trades, "strategy"),
        "cost_total": sum(float(trade.get("fees") or 0.0) for trade in trades),
        "slippage_total": sum(float(trade.get("slippage") or 0.0) for trade in trades),
        "cost_percent_of_positive_gross_pnl": _cost_percent_of_positive_gross(trades),
        "positive_gross_destroyed_by_costs": sum(
            1
            for trade in trades
            if float(trade.get("gross_pnl") or 0.0) > 0
            and float(trade.get("fees") or 0.0) + float(trade.get("slippage") or 0.0)
            > float(trade.get("gross_pnl") or 0.0)
        ),
    }


def _pnl_bucket(trades: list[dict[str, Any]], field: str) -> dict[str, dict[str, float]]:
    buckets: dict[str, dict[str, float]] = defaultdict(lambda: {"trade_count": 0, "pnl": 0.0})
    for trade in trades:
        key = str(trade.get(field) or "unknown")
        buckets[key]["trade_count"] += 1
        buckets[key]["pnl"] += float(trade.get("net_pnl") or 0.0)
    return dict(buckets)


def _cost_percent_of_positive_gross(trades: list[dict[str, Any]]) -> float | None:
    positive_gross = sum(
        float(trade.get("gross_pnl") or 0.0)
        for trade in trades
        if float(trade.get("gross_pnl") or 0.0) > 0
    )
    costs = sum(float(trade.get("fees") or 0.0) for trade in trades)
    return costs / positive_gross if positive_gross else None


def _filter_summary(trades: list[dict[str, Any]], predicate) -> dict[str, Any]:
    selected = [trade for trade in trades if predicate(trade)]
    pnl_values = [float(trade["net_pnl"]) for trade in selected]
    return {
        "trade_count": len(selected),
        "pnl": sum(pnl_values),
        "average_pnl": sum(pnl_values) / len(pnl_values) if pnl_values else 0.0,
        "winning_trades": sum(1 for value in pnl_values if value > 0),
        "losing_trades": sum(1 for value in pnl_values if value < 0),
        "approx_drawdown": _max_drawdown(pnl_values),
    }


def _max_drawdown(pnl_values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for pnl in pnl_values:
        equity += pnl
        peak = max(peak, equity)
        max_dd = min(max_dd, equity - peak)
    return max_dd


def _recommendations(causes: dict[str, Any], filter_results: dict[str, Any]) -> list[str]:
    recommendations = [
        "Ne pas augmenter la taille des runs tant que le post-mortem reste negatif.",
        "Ajouter au prompt une contrainte risk/reward minimale avant validation active.",
        "Rendre le modele explicitement cost-aware avant de valider un setup acceptable.",
    ]
    if causes.get("setup_quality seulement acceptable"):
        recommendations.append("Tester un filtre temporaire: n'executer que good/excellent.")
    if causes.get("frais/slippage eleves vs potentiel"):
        recommendations.append(
            "Refuser les setups dont le potentiel attendu couvre mal frais et slippage."
        )
    if filter_results.get("setup_quality_score_gte_0_6", {}).get("trade_count", 0) == 0:
        recommendations.append(
            "Demander un score plus discriminant: acceptable faible ne doit pas suffire."
        )
    return recommendations


def _market_regime(review: dict[str, Any]) -> Any:
    raw = json.dumps(review, ensure_ascii=False)
    if "uptrend" in raw:
        return "uptrend"
    if "downtrend" in raw:
        return "downtrend"
    if "range" in raw:
        return "range"
    return "unknown"


def _trend_from_review(review: dict[str, Any], trend: str) -> str:
    raw = json.dumps(review, ensure_ascii=False).lower()
    if f"{trend}=up" in raw or f"{trend} is up" in raw:
        return "up"
    if f"{trend}=down" in raw or f"{trend} is down" in raw:
        return "down"
    return "unknown"


def _volatility_from_review(review: dict[str, Any]) -> str:
    raw = json.dumps(review, ensure_ascii=False).lower()
    if "volatilite normale" in raw or "volatility is normal" in raw or "normal" in raw:
        return "normal"
    if "volatility" in raw or "volatil" in raw:
        return "mentioned"
    return "unknown"


def _derivatives_available(review: dict[str, Any]) -> list[str]:
    raw = json.dumps(review, ensure_ascii=False).lower()
    return [key for key in ["funding", "open_interest", "basis"] if f"{key} available" in raw]


def _derivatives_unavailable(review: dict[str, Any]) -> list[str]:
    raw = json.dumps(review, ensure_ascii=False).lower()
    keys = []
    if "derivatives" in raw or "derives" in raw or "dériv" in raw:
        keys.extend(["funding", "open_interest", "basis", "liquidations"])
    return keys


def _safe_json(raw: Any) -> dict[str, Any]:
    try:
        payload = json.loads(raw or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
