from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from galapagos.agent.decision_validator import validate_decision_context
from galapagos.agent.llm_client import LLMDecisionClient
from galapagos.agent.llm_providers import MockLLMProvider, OpenAICodexProvider
from galapagos.analysis.performance import summarize_profile_performance
from galapagos.data.binance_futures_collector import (
    BinanceFuturesCollector,
    derivatives_availability_summary,
    unavailable_derivatives,
    unavailable_features,
)
from galapagos.data.data_normalizer import normalize_ohlcv
from galapagos.data.data_quality import assess_ohlcv_quality
from galapagos.data.kraken_collector import KrakenCollector, mock_ohlcv
from galapagos.data.market_snapshot import MarketSnapshot
from galapagos.execution.paper_state import PaperState
from galapagos.indicators.market_regime import detect_market_regime
from galapagos.indicators.technical_indicators import compute_technical_indicators
from galapagos.indicators.volatility import realized_volatility
from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.risk.risk_engine import RiskEngine
from galapagos.strategies.scenario_builder import build_scenarios
from galapagos.utils.time_utils import utc_now_iso


def build_market_snapshot(
    profile: dict[str, Any],
    *,
    use_real_data: bool = False,
) -> MarketSnapshot:
    if use_real_data:
        raw = KrakenCollector().fetch_ohlcv(profile["symbol"], profile["timeframe"])
        derivatives = BinanceFuturesCollector().fetch_derivatives_snapshot("BTC/USDT:USDT")
    else:
        raw = mock_ohlcv()
        derivatives = unavailable_derivatives("BTC/USDT:USDT")
    ohlcv = normalize_ohlcv(raw)
    indicators = compute_technical_indicators(ohlcv)
    vol = realized_volatility(ohlcv)
    indicators["realized_volatility"] = vol
    regime = detect_market_regime(indicators, vol)
    indicators["market_regime"] = regime
    scenarios = build_scenarios(indicators, regime, derivatives)
    quality = assess_ohlcv_quality(ohlcv)
    quality["data_mode"] = "real" if use_real_data else "mock"
    quality["derivatives_status"] = derivatives
    source_timestamp = ohlcv["timestamp"].iloc[-1]
    collected_at = utc_now_iso()
    freshness = _freshness_seconds(source_timestamp, collected_at)
    deriv_summary = derivatives_availability_summary(derivatives)
    unavailable = unavailable_features(derivatives)
    quality["derivatives_availability_summary"] = deriv_summary
    quality["unavailable_features"] = unavailable
    quality["data_freshness_seconds"] = freshness
    market = {
        "last_open": float(ohlcv["open"].iloc[-1]),
        "last_high": float(ohlcv["high"].iloc[-1]),
        "last_low": float(ohlcv["low"].iloc[-1]),
        "last_close": indicators["last_close"],
        "last_volume": indicators["last_volume"],
        "source": "kraken_ccxt" if use_real_data else "mock_ohlcv",
    }
    return MarketSnapshot(
        profile=profile["name"],
        asset=profile["symbol"],
        timeframe=profile["timeframe"],
        market=market,
        indicators=indicators,
        derivatives=derivatives,
        scenarios=scenarios,
        data_quality=quality,
        collected_at_utc=collected_at,
        source_timestamps={"ohlcv_last": str(source_timestamp)},
        data_mode=quality["data_mode"],
        data_freshness_seconds=freshness,
        derivatives_availability_summary=deriv_summary,
        unavailable_features=unavailable,
    )


def run_cycle(
    *,
    profile: dict[str, Any],
    risk_config: dict[str, Any],
    llm_config: dict[str, Any],
    database_path: str,
    use_real_data: bool = False,
    use_mock_llm: bool = True,
    mock_decision: str = "NO_TRADE",
) -> dict[str, Any]:
    store = SQLiteStore(database_path)
    snapshot = build_market_snapshot(profile, use_real_data=use_real_data)
    snapshot_payload = snapshot.to_dict()
    snapshot_id = store.insert_market_snapshot(snapshot_payload)
    paper_state = PaperState(
        store,
        initial_capital=float(risk_config["simulated_initial_capital"]),
        profile=profile["name"],
    )
    broker = paper_state.load_broker()
    candle = {
        "high": snapshot.market["last_high"],
        "low": snapshot.market["last_low"],
        "close": snapshot.market["last_close"],
    }
    exit_events = broker.evaluate_position_exits(
        candle=candle,
        kill_switch_active=(
            snapshot.data_quality.get("status") != "available"
            or snapshot.indicators.get("market_regime", {}).get("volatility_regime") == "extreme"
        ),
    )
    for event in exit_events:
        store.insert_paper_trade(event["trade"])

    provider = MockLLMProvider(mock_decision) if use_mock_llm else OpenAICodexProvider(llm_config)
    client = LLMDecisionClient(provider)
    context = {
        "profile": profile,
        "market": snapshot.market,
        "indicators": snapshot.indicators,
        "derivatives": snapshot.derivatives,
        "scenarios": snapshot.scenarios,
        "data_quality": snapshot.data_quality,
        "derivatives_availability_summary": snapshot.derivatives_availability_summary,
        "unavailable_features": snapshot.unavailable_features,
    }
    try:
        decision, raw_response, validity = client.decide(context)
        validation = validate_decision_context(
            decision,
            profile=profile,
            market=snapshot.market,
            derivatives=snapshot.derivatives,
            config=llm_config,
        )
        decision = validation.decision
        if validation.validity != "valid_schema":
            validity = validation.validity
            store.insert_system_event(
                {
                    "timestamp_utc": utc_now_iso(),
                    "level": "WARNING",
                    "message": "LLM context validation fallback produced NO_TRADE.",
                    "payload": {"reasons": validation.reasons},
                }
            )
        elif validity == "parser_fallback":
            store.insert_system_event(
                {
                    "timestamp_utc": utc_now_iso(),
                    "level": "WARNING",
                    "message": "LLM parser fallback produced NO_TRADE.",
                    "payload": {"raw_response": raw_response},
                }
            )
    except Exception as exc:  # noqa: BLE001
        from galapagos.agent.decision_schema import no_trade_decision

        decision = no_trade_decision(
            profile=profile["name"],
            asset=profile["symbol"],
            horizon=profile["timeframe"],
            reason=f"LLM provider failure: {exc}",
        )
        raw_response = str(exc)
        validity = "provider_failure_fallback"

    risk = RiskEngine(risk_config).evaluate(
        decision,
        profile_config=profile,
        data_available=snapshot.data_quality.get("status") == "available",
        volatility_regime=snapshot.indicators.get("market_regime", {}).get("volatility_regime"),
        open_positions=list(broker.positions.values()),
        current_price=snapshot.market["last_close"],
        current_capital=broker.cash,
    )
    if risk.approved:
        execution_event = broker.execute_decision(
            decision,
            approved_risk_fraction=risk.adjusted_risk_fraction,
            current_price=snapshot.market["last_close"],
        )
    else:
        execution_event = {
            "action": "RISK_REJECTED",
            "status": "NO_EXECUTION",
            "reasons": risk.reasons,
        }
        store.insert_system_event(
            {
                "timestamp_utc": utc_now_iso(),
                "level": "WARNING",
                "message": "Risk engine rejected decision; no paper execution.",
                "payload": execution_event,
            }
        )
    if execution_event.get("trade"):
        store.insert_paper_trade(execution_event["trade"])
    paper_state.save_broker(broker)
    timestamp = utc_now_iso()
    decision_id = store.insert_agent_decision(
        {
            "timestamp_utc": timestamp,
            "profile": decision.profile,
            "asset": decision.asset,
            "timeframe": decision.horizon,
            "input_context_hash": snapshot.content_hash(),
            "market_snapshot_id": snapshot_id,
            "raw_llm_response": raw_response,
            "parsed_decision": decision.model_dump(mode="json"),
            "decision_validity": validity,
            "risk_engine_result": asdict(risk),
            "final_action": risk.final_action.value,
            "reasoning_summary": decision.reasoning_summary,
            "critical_data_used": decision.critical_data_used,
        }
    )
    store.insert_risk_decision(
        {
            "timestamp_utc": timestamp,
            "agent_decision_id": decision_id,
            "approved": risk.approved,
            "final_action": risk.final_action.value,
            "reasons": risk.reasons,
        }
    )
    trades = [
        dict(row)
        for row in store.query("SELECT * FROM paper_trades WHERE profile = ?", (profile["name"],))
    ]
    decisions = [
        dict(row)
        for row in store.query(
            "SELECT * FROM agent_decisions WHERE profile = ?",
            (profile["name"],),
        )
    ]
    open_positions = [position.__dict__ for position in broker.positions.values()]
    metrics = summarize_profile_performance(
        profile=profile["name"],
        trades=trades,
        open_positions=open_positions,
        decisions=decisions,
        current_price=snapshot.market["last_close"],
    )
    store.insert_performance_snapshot(
        {
            "timestamp_utc": utc_now_iso(),
            "profile": profile["name"],
            "cash": broker.cash,
            "equity": broker.mark_to_market(snapshot.market["last_close"]),
            "metrics": metrics,
        }
    )
    return {
        "snapshot": snapshot_payload,
        "decision": decision.model_dump(mode="json"),
        "risk": asdict(risk),
        "execution": execution_event,
        "position_exit_events": exit_events,
        "open_positions": open_positions,
        "account": {
            "cash": broker.cash,
            "equity": broker.mark_to_market(snapshot.market["last_close"]),
        },
        "performance": metrics,
        "llm_provider_status": provider.status,
        "database_path": database_path,
    }


def _freshness_seconds(source_timestamp: Any, collected_at: str) -> float | None:
    try:
        if hasattr(source_timestamp, "to_pydatetime"):
            source_dt = source_timestamp.to_pydatetime()
        elif isinstance(source_timestamp, datetime):
            source_dt = source_timestamp
        else:
            source_dt = datetime.fromisoformat(str(source_timestamp))
        if source_dt.tzinfo is None:
            source_dt = source_dt.replace(tzinfo=UTC)
        collected_dt = datetime.fromisoformat(collected_at)
        return max(0.0, (collected_dt - source_dt).total_seconds())
    except (TypeError, ValueError):
        return None
