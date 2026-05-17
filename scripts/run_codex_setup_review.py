from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.agent.decision_cache import (
    DecisionCache,
    DecisionCacheEntry,
    build_decision_cache_key,
    stable_json_hash,
    utc_now_iso,
)
from galapagos.agent.decision_context import build_decision_context
from galapagos.agent.decision_parser import parse_decision_response_with_metadata
from galapagos.agent.decision_postprocessor import postprocess_decision_for_risk
from galapagos.agent.decision_prompt import build_llm_decision_prompt
from galapagos.agent.decision_schema import no_trade_decision
from galapagos.agent.decision_validator import validate_decision_context
from galapagos.agent.llm_providers import CodexCLIProvider
from galapagos.agent.trade_constraints import apply_trade_constraints
from galapagos.backtest.candidate_selector import (
    build_policy_context,
    candidate_to_dict,
    select_candidate_setups,
)
from galapagos.backtest.historical_data import find_latest_cached_ohlcv, load_historical_ohlcv
from galapagos.backtest.timeframe_utils import candle_close_time
from galapagos.execution.exit_policy import apply_exit_policy
from galapagos.execution.paper_broker import PaperBroker
from galapagos.risk.risk_engine import RiskEngine
from galapagos.utils.config_loader import load_profile, load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="4h")
    parser.add_argument("--max-candidates", type=int, default=20)
    parser.add_argument("--source-policies", default="state_aware_breakout,state_aware_momentum")
    parser.add_argument("--allow-codex-cli", action="store_true")
    parser.add_argument("--provider", choices=["codex_cli", "mock"], default="codex_cli")
    parser.add_argument("--data-path", default=None)
    parser.add_argument("--output-dir", default="reports/backtests")
    parser.add_argument("--output-prefix", default="codex_setup_review_v1_8C_9")
    parser.add_argument("--version", default="V1.8C.9")
    parser.add_argument("--window-label", default=None)
    parser.add_argument("--evaluation-run-id", default=None)
    parser.add_argument("--evaluation-config", default=None)
    parser.add_argument("--use-decision-cache", action="store_true")
    parser.add_argument("--cache-readonly", action="store_true")
    parser.add_argument("--cache-write", action="store_true")
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--cached-decisions-json", default=None)
    args = parser.parse_args()
    if args.profile != "4h":
        raise RuntimeError("V1.8C.9 setup review is limited to profile 4h.")
    if args.max_candidates > 20 and args.provider == "codex_cli":
        raise RuntimeError("V1.8C.9 is limited to 20 Codex CLI calls.")
    if (
        args.provider == "codex_cli"
        and not args.allow_codex_cli
        and not (args.use_decision_cache and args.cache_readonly)
        and not args.cached_decisions_json
    ):
        raise RuntimeError("Codex setup review requires --allow-codex-cli.")

    profile = load_profile(args.profile)
    data_path = Path(args.data_path) if args.data_path else find_latest_cached_ohlcv(
        profile["symbol"], profile["timeframe"]
    )
    if data_path is None:
        raise RuntimeError("No cached OHLCV data found. Run download_historical_ohlcv first.")
    risk_config = load_yaml("configs/risk.yaml")
    llm_config = load_yaml("configs/llm.yaml")
    evaluation_config = load_yaml(args.evaluation_config) if args.evaluation_config else {}
    trade_constraints = evaluation_config.get("trade_constraints") or {}
    exit_policy_config = evaluation_config.get("exit_policy") or {}
    evaluation_options = evaluation_config.get("evaluation") or {}
    llm_config["allow_codex_cli_calls"] = bool(args.allow_codex_cli)
    provider = CodexCLIProvider(llm_config) if args.provider == "codex_cli" else None
    cache = DecisionCache() if args.use_decision_cache else None
    cached_decisions = _load_cached_decisions_map(args.cached_decisions_json)
    provider_model = str(
        (llm_config.get("codex_cli") or {}).get("model")
        or llm_config.get("model")
        or "gpt-5.5"
    )
    provider_reasoning = str(
        (llm_config.get("codex_cli") or {}).get("reasoning_effort")
        or llm_config.get("reasoning_effort")
        or "low"
    )
    constraints_config_hash = stable_json_hash(
        {
            "trade_constraints": trade_constraints,
            "exit_policy": exit_policy_config,
            "evaluation": evaluation_options,
        }
    )
    source_policies = [item.strip() for item in args.source_policies.split(",") if item.strip()]
    candidates = sorted(
        select_candidate_setups(
            profile=profile,
            data_path=data_path,
            source_policies=source_policies,
            max_candidates=args.max_candidates,
        ),
        key=lambda candidate: candidate.decision_timestamp,
    )
    data = _with_candle_times(load_historical_ohlcv(data_path).reset_index(drop=True), profile)
    broker = PaperBroker(initial_capital=10_000)
    reviews = []
    trades = []
    closed_trades_ledger = []
    position_events = []
    open_position_metadata = {}
    recent_decisions = []
    recent_trades = []
    run_id = args.evaluation_run_id or str(uuid4())
    last_exit_index = -1
    for candidate in candidates:
        for candle_index in range(last_exit_index + 1, candidate.context_index + 1):
            if not broker.positions:
                continue
            candle = data.iloc[candle_index].to_dict()
            closed_events = broker.evaluate_position_exits(
                candle=candle,
                timestamp=str(data["candle_close_timestamp"].iloc[candle_index]),
            )
            for closed in closed_events:
                if closed.get("trade"):
                    trade = closed["trade"]
                    trades.append(trade)
                    recent_trades.append(trade)
                    metadata = open_position_metadata.pop(trade.get("id"), {})
                    closed_trades_ledger.append(
                        _ledger_entry(
                            trade,
                            metadata,
                            candidate_id_exit=None,
                            exit_decision=None,
                            exit_context_hash=None,
                            exit_context_index=candle_index,
                        )
                    )
                    position_events.append(
                        _position_event(
                            timestamp=str(data["candle_close_timestamp"].iloc[candle_index]),
                            candidate_id=None,
                            event_type="auto_close",
                            position_id=trade.get("id"),
                            decision=None,
                            price=trade.get("exit_price"),
                            reason=trade.get("close_reason"),
                            fees=trade.get("exit_fee"),
                            slippage=trade.get("exit_slippage"),
                            pnl_delta=trade.get("pnl"),
                        )
                    )
        last_exit_index = candidate.context_index
        context = build_policy_context(profile, data.iloc[: candidate.context_index + 1].copy())
        context["portfolio"] = _portfolio_from_broker(
            broker,
            profile,
            current_price=float(context["market"]["last_close"]),
            timestamp=candidate.decision_timestamp,
        )
        decision_context = build_decision_context(
            profile=profile,
            market=context["market"],
            indicators=context["indicators"],
            derivatives=context["derivatives"],
            scenarios=context["scenarios"],
            portfolio=context["portfolio"],
            risk_config=risk_config,
            decision_timestamp=candidate.decision_timestamp,
            data_mode="historical_setup_review",
            run_id=run_id,
            ohlcv_window=context["ohlcv_window"],
            recent_decisions=recent_decisions,
            recent_trades=recent_trades,
            candidate_setup=candidate_to_dict(candidate),
        )
        decision_context_payload = decision_context.to_dict()
        prompt = build_llm_decision_prompt(decision_context, prompt_mode="setup_review")
        prompt = _apply_prompt_trade_constraints(prompt, trade_constraints)
        cache_context_hash = _cache_context_hash(
            candidate=candidate,
            portfolio=context["portfolio"],
            trade_constraints=trade_constraints,
        )
        prompt_hash = stable_json_hash(
            {
                "prompt_mode": "setup_review",
                "prompt_contract": "v1.10.5",
                "trade_constraints": trade_constraints,
            }
        )
        cache_key = build_decision_cache_key(
            context_hash=cache_context_hash,
            prompt_hash=prompt_hash,
            model=provider_model,
            reasoning_effort=provider_reasoning,
            prompt_mode="setup_review",
            constraints_config_hash=constraints_config_hash,
        )
        mapped_raw = cached_decisions.get(candidate.candidate_id)
        cache_entry = None if cache is None or args.refresh_cache else cache.get(cache_key)
        cache_status = "disabled"
        cache_path = None
        if mapped_raw is not None:
            cache_status = "external_hit"
            provider_result = _external_cached_provider_result(mapped_raw)
        elif cached_decisions:
            raise RuntimeError(f"Cached decision missing for candidate {candidate.candidate_id}")
        elif cache_entry is not None:
            cache_status = "hit"
            provider_result = _cached_provider_result(cache_entry)
        elif cache is not None:
            cache_status = "miss"
            if args.cache_readonly:
                provider_result = _readonly_cache_miss_result(
                    candidate,
                    profile,
                    cache_key.cache_key,
                )
            else:
                if provider is None:
                    provider_result = _mock_provider_result(candidate, profile)
                elif not args.allow_codex_cli:
                    provider_result = _readonly_cache_miss_result(
                        candidate,
                        profile,
                        cache_key.cache_key,
                    )
                else:
                    provider_result = provider.generate(prompt)
        else:
            provider_result = (
                provider.generate(prompt)
                if provider is not None
                else _mock_provider_result(candidate, profile)
            )
        raw = provider_result.raw_response or _fallback_raw(
            candidate,
            profile,
            provider_result.error,
        )
        parsed = parse_decision_response_with_metadata(
            raw,
            profile["name"],
            profile["symbol"],
            profile["timeframe"],
        )
        validation = validate_decision_context(
            parsed.decision,
            profile=profile,
            market=context["market"],
            derivatives=context["derivatives"],
            config=llm_config,
        )
        parsed_decision = validation.decision
        postprocessed = postprocess_decision_for_risk(
            parsed_decision,
            decision_context=decision_context,
            config=llm_config,
        )
        if (
            cache is not None
            and cache_entry is None
            and (args.cache_write or args.refresh_cache)
            and provider_result.raw_response
            and not provider_result.error
        ):
            entry = DecisionCacheEntry(
                cache_key=cache_key.cache_key,
                context_hash=cache_key.context_hash,
                prompt_hash=cache_key.prompt_hash,
                model=cache_key.model,
                reasoning_effort=cache_key.reasoning_effort,
                prompt_mode=cache_key.prompt_mode,
                constraints_config_hash=cache_key.constraints_config_hash,
                created_at_utc=utc_now_iso(),
                provider_name=provider_result.provider_name,
                raw_response=raw,
                parsed_decision=parsed.decision.model_dump(mode="json"),
                decision_validity=parsed.validity,
                parser_repair_applied=parsed.parser_repair_applied,
                postprocessing_warnings=postprocessed.warnings,
                safety_warnings=[],
                duration_seconds=provider_result.duration_seconds,
                codex_exit_code=provider_result.exit_code,
                stdout_preview=provider_result.stdout_preview,
                stderr_preview=provider_result.stderr_preview,
            )
            cache_path = str(cache.put(cache_key, entry))
            cache_status = "written"
        constrained = apply_trade_constraints(postprocessed.decision, trade_constraints)
        variant_filtered = _apply_variant_filters(
            constrained.decision,
            decision_context_payload=decision_context_payload,
            filter_config=evaluation_config,
        )
        exit_policy_result = apply_exit_policy(
            variant_filtered["decision"],
            portfolio=context["portfolio"],
            config=exit_policy_config,
        )
        decision = exit_policy_result.decision
        risk = RiskEngine(risk_config).evaluate(
            decision,
            profile_config=profile,
            data_available=True,
            volatility_regime=context["indicators"].get("market_regime", {}).get(
                "volatility_regime"
            ),
            open_positions=list(broker.positions.values()),
            current_price=context["market"]["last_close"],
            current_capital=broker.cash,
        )
        event = {"action": "NO_EXECUTION", "status": "RISK_REJECTED_OR_NO_TRADE"}
        if risk.approved:
            event = broker.execute_decision(
                decision,
                approved_risk_fraction=risk.adjusted_risk_fraction,
                current_price=context["market"]["last_close"],
                timestamp=candidate.decision_timestamp,
            )
            if event.get("trade"):
                trade = event["trade"]
                trades.append(trade)
                recent_trades.append(trade)
                metadata = open_position_metadata.pop(trade.get("id"), {})
                closed_trades_ledger.append(
                    _ledger_entry(
                        trade,
                        metadata,
                        candidate_id_exit=candidate.candidate_id,
                        exit_decision=_safe_json(raw),
                        exit_context_hash=decision_context_payload.get("context_hash"),
                        exit_context_index=candidate.context_index,
                    )
                )
                position_events.append(
                    _position_event(
                        timestamp=candidate.decision_timestamp,
                        candidate_id=candidate.candidate_id,
                        event_type="close",
                        position_id=trade.get("id"),
                        decision=decision.decision.value,
                        price=trade.get("exit_price"),
                        reason=trade.get("close_reason"),
                        fees=trade.get("exit_fee"),
                        slippage=trade.get("exit_slippage"),
                        pnl_delta=trade.get("pnl"),
                    )
                )
            if event.get("position"):
                position = event["position"]
                open_position_metadata[position["id"]] = _entry_metadata(
                    candidate=candidate,
                    decision_payload=_safe_json(raw),
                    decision_context=decision_context_payload,
                    context=context,
                )
                position_events.append(
                    _position_event(
                        timestamp=candidate.decision_timestamp,
                        candidate_id=candidate.candidate_id,
                        event_type="open",
                        position_id=position.get("id"),
                        decision=decision.decision.value,
                        price=position.get("entry_price"),
                        reason=None,
                        fees=position.get("entry_fee"),
                        slippage=position.get("entry_slippage"),
                        pnl_delta=0.0,
                    )
                )
        elif risk.reasons:
            position_events.append(
                _position_event(
                    timestamp=candidate.decision_timestamp,
                    candidate_id=candidate.candidate_id,
                    event_type="risk_reject",
                    position_id=None,
                    decision=decision.decision.value,
                    price=context["market"]["last_close"],
                    reason="; ".join(risk.reasons),
                    fees=0.0,
                    slippage=0.0,
                    pnl_delta=0.0,
                )
            )
        recent_decision = {
            "decision": decision.decision.value,
            "risk_approved": risk.approved,
            "timestamp": candidate.decision_timestamp,
        }
        recent_decisions.append(recent_decision)
        reviews.append(
            {
                "candidate": candidate_to_dict(candidate),
                "raw_response": raw,
                "decision": decision.decision.value,
                "raw_decision": parsed.decision.decision.value,
                "decision_before_postprocessing": parsed_decision.decision.value,
                "decision_after_postprocessing": postprocessed.decision.decision.value,
                "decision_after_constraints": constrained.decision.decision.value,
                "decision_after_variant_filters": variant_filtered["decision"].decision.value,
                "decision_after_exit_policy": decision.decision.value,
                "final_decision": decision.decision.value,
                "baseline_decision": candidate.baseline_decision,
                "parser_validity": parsed.validity,
                "parser_repair_applied": parsed.parser_repair_applied,
                "raw_json_valid": parsed.raw_json_valid,
                "parser_error": parsed.error,
                "enum_violations": parsed.enum_violations or [],
                "raw_response_preview": raw[:1000],
                "response_length": len(raw),
                "context_validity": validation.validity,
                "postprocessing_action": postprocessed.action,
                "postprocessing_warnings": postprocessed.warnings,
                "postprocessing_missing_required": postprocessed.missing_required,
                "stateful_safety_override": postprocessed.stateful_override,
                "original_decision": constrained.original_decision,
                "postprocessor_original_decision": postprocessed.original_decision,
                "constraint_override": constrained.constraint_override,
                "constraint_action": constrained.action,
                "constraint_warnings": constrained.warnings,
                "trade_constraints": trade_constraints,
                "variant_filter_action": variant_filtered["action"],
                "blocked_by_cost_filter": variant_filtered["blocked_by_cost_filter"],
                "blocked_by_regime_filter": variant_filtered["blocked_by_regime_filter"],
                "cost_filter_ratio": variant_filtered["cost_ratio"],
                "regime_filter_reason": variant_filtered["regime_reason"],
                "exit_policy_override": exit_policy_result.exit_policy_override,
                "exit_policy_action": exit_policy_result.action,
                "exit_policy_warnings": exit_policy_result.warnings,
                "bars_in_position": exit_policy_result.bars_in_position,
                "min_holding_bars": exit_policy_result.min_holding_bars,
                "portfolio_before_decision": context["portfolio"],
                "risk_approved": risk.approved,
                "risk_reasons": risk.reasons,
                "provider_duration_seconds": provider_result.duration_seconds,
                "provider_error": provider_result.error,
                "provider_stdout_preview": provider_result.stdout_preview,
                "provider_stderr_preview": provider_result.stderr_preview,
                "execution_event": event,
                "context_hash": decision_context_payload.get("context_hash"),
                "prompt_hash": prompt_hash,
                "cache_context_hash": cache_context_hash,
                "decision_cache_key": cache_key.cache_key if cache is not None else None,
                "decision_cache_status": cache_status,
                "decision_cache_path": cache_path,
            }
        )
    if evaluation_options.get("force_close_at_end"):
        _force_close_open_positions_at_window_end(
            broker=broker,
            data=data,
            trades=trades,
            recent_trades=recent_trades,
            closed_trades_ledger=closed_trades_ledger,
            position_events=position_events,
            open_position_metadata=open_position_metadata,
        )
    report = _build_report(
        candidates,
        reviews,
        trades,
        data,
        broker,
        closed_trades_ledger,
        position_events,
    )
    report["version"] = args.version
    report["window_label"] = args.window_label
    report["evaluation_run_id"] = args.evaluation_run_id
    report["safety"] = f"Le systeme {args.version} ne peut toujours pas passer d'ordre reel."
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / f"{args.output_prefix}.json"
    md_path = output / f"{args.output_prefix}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {"markdown": str(md_path), "json": str(json_path), **report},
            indent=2,
            ensure_ascii=False,
        )
    )


class _MockResult:
    provider_name = "mock"
    raw_response: str
    exit_code = None
    duration_seconds = 0.0
    error = None
    stdout_preview = ""
    stderr_preview = ""

    def __init__(self, raw_response: str) -> None:
        self.raw_response = raw_response


class _CachedResult:
    def __init__(self, entry: DecisionCacheEntry) -> None:
        self.provider_name = entry.provider_name
        self.raw_response = entry.raw_response
        self.exit_code = entry.codex_exit_code
        self.duration_seconds = 0.0
        self.error = None
        self.stdout_preview = "decision_cache_hit"
        self.stderr_preview = ""


def _cached_provider_result(entry: DecisionCacheEntry) -> _CachedResult:
    return _CachedResult(entry)


class _ExternalCachedResult:
    provider_name = "decision_cache"
    exit_code = None
    duration_seconds = 0.0
    error = None
    stdout_preview = "external_cached_decision"
    stderr_preview = ""

    def __init__(self, raw_response: str) -> None:
        self.raw_response = raw_response


def _external_cached_provider_result(raw_response: str) -> _ExternalCachedResult:
    return _ExternalCachedResult(raw_response)


def _load_cached_decisions_map(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in payload.items()}


def _readonly_cache_miss_result(candidate, profile, cache_key: str) -> _MockResult:
    result = _MockResult(
        _fallback_raw(
            candidate,
            profile,
            f"Decision cache miss in readonly mode: {cache_key}",
        )
    )
    result.error = f"decision_cache_miss_readonly:{cache_key}"
    return result


def _mock_provider_result(candidate, profile):
    return _MockResult(_fallback_raw(candidate, profile, None))


def _fallback_raw(candidate, profile, error):
    return json.dumps(
        {
            "decision": "NO_TRADE",
            "profile": profile["name"],
            "asset": profile["symbol"],
            "strategy": "no_trade",
            "confidence": 0.0,
            "reasoning_summary": error or "Mock setup review fallback.",
            "horizon": profile["timeframe"],
            "reference_entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "risk_fraction": 0.0,
            "max_duration_minutes": 0,
            "invalidation_conditions": [],
            "critical_data_used": [],
            "setup_quality": "poor",
            "setup_quality_score": 0.0,
            "why_not_no_trade": None,
        }
    )


def _apply_prompt_trade_constraints(prompt: str, trade_constraints: dict) -> str:
    if not trade_constraints:
        return prompt
    lines = ["", "Experiment trade constraints:"]
    if trade_constraints.get("allow_short") is False:
        lines.append("- SHORT decisions are disabled in this experiment.")
        lines.append("- If you would short, answer NO_TRADE.")
    if trade_constraints.get("allow_long") is False:
        lines.append("- LONG decisions are disabled in this experiment.")
        lines.append("- If you would go long, answer NO_TRADE.")
    if trade_constraints.get("allow_hold") is False:
        lines.append("- HOLD decisions are disabled in this experiment.")
    if trade_constraints.get("allow_close") is False:
        lines.append("- CLOSE decisions are disabled in this experiment.")
    return prompt + "\n" + "\n".join(lines)


def _force_close_open_positions_at_window_end(
    *,
    broker,
    data,
    trades,
    recent_trades,
    closed_trades_ledger,
    position_events,
    open_position_metadata,
) -> None:
    if not broker.positions or len(data) == 0:
        return
    last_index = len(data) - 1
    timestamp = str(data["candle_close_timestamp"].iloc[last_index])
    exit_price = float(data["close"].iloc[last_index])
    for position_id in list(broker.positions):
        trade = broker.close_position(
            position_id,
            exit_price=exit_price,
            reason="evaluation_window_end",
            timestamp=timestamp,
        )
        trades.append(trade)
        recent_trades.append(trade)
        metadata = open_position_metadata.pop(trade.get("id"), {})
        closed_trades_ledger.append(
            _ledger_entry(
                trade,
                metadata,
                candidate_id_exit=None,
                exit_decision=None,
                exit_context_hash=None,
                exit_context_index=last_index,
            )
        )
        position_events.append(
            _position_event(
                timestamp=timestamp,
                candidate_id=None,
                event_type="auto_close",
                position_id=trade.get("id"),
                decision=None,
                price=trade.get("exit_price"),
                reason="evaluation_window_end",
                fees=trade.get("exit_fee"),
                slippage=trade.get("exit_slippage"),
                pnl_delta=trade.get("pnl"),
            )
        )


def _build_report(
    candidates,
    reviews,
    trades,
    data,
    broker,
    closed_trades_ledger,
    position_events,
):
    distribution = Counter(review["decision"] for review in reviews)
    raw_distribution = Counter(review.get("raw_decision") for review in reviews)
    constrained_distribution = Counter(
        review.get("decision_after_constraints") for review in reviews
    )
    exit_policy_distribution = Counter(
        review.get("decision_after_exit_policy") for review in reviews
    )
    baseline_distribution = Counter(candidate.baseline_decision for candidate in candidates)
    active = {"LONG", "SHORT"}
    validated = sum(1 for review in reviews if review["decision"] in active)
    rejected = sum(1 for review in reviews if review["decision"] == "NO_TRADE")
    baseline_active = len(candidates)
    baseline_outcomes = _outcome_comparison(candidates, reviews, data)
    official_pnl = sum(float(trade.get("pnl") or 0.0) for trade in trades)
    ledger_pnl = sum(float(trade.get("net_pnl") or 0.0) for trade in closed_trades_ledger)
    unrealized_pnl = broker.mark_to_market(_last_price(data)) - broker.cash
    final_equity_pnl = official_pnl + unrealized_pnl
    trade_count = len(trades)
    return {
        "version": "V1.8C.9",
        "candidates_found": len(candidates),
        "candidates_submitted": len(reviews),
        "json_valid_rate": _rate(
            sum(1 for review in reviews if review["parser_validity"] == "valid_schema"),
            len(reviews),
        ),
        "raw_json_valid_rate": _rate(
            sum(1 for review in reviews if review.get("raw_json_valid")),
            len(reviews),
        ),
        "repaired_json_count": sum(
            1 for review in reviews if review.get("parser_repair_applied")
        ),
        "final_parse_success_rate": _rate(
            sum(1 for review in reviews if review["parser_validity"] != "parser_fallback"),
            len(reviews),
        ),
        "fallback_count": sum(
            1 for review in reviews if review["parser_validity"] != "valid_schema"
        ),
        "strict_parser_fallback_count": sum(
            1 for review in reviews if review["parser_validity"] == "parser_fallback"
        ),
        "enum_violations_count": sum(
            len(review.get("enum_violations") or []) for review in reviews
        ),
        "top_enum_violations": _top_enum_violations(reviews),
        "setup_quality_distribution": _setup_quality_distribution(reviews),
        "setup_quality_score_average": _setup_quality_score_average(reviews),
        "decision_distribution": dict(distribution),
        "raw_decision_distribution": dict(raw_distribution),
        "decision_after_constraints_distribution": dict(constrained_distribution),
        "decision_after_exit_policy_distribution": dict(exit_policy_distribution),
        "baseline_distribution": dict(baseline_distribution),
        "validation_rate": _rate(validated, len(reviews)),
        "refusal_rate": _rate(rejected, len(reviews)),
        "risk_rejects": sum(1 for review in reviews if not review["risk_approved"]),
        "hold_count": distribution.get("HOLD", 0),
        "close_count": distribution.get("CLOSE", 0),
        "stateful_overrides": sum(1 for review in reviews if review["stateful_safety_override"]),
        "constraint_overrides": sum(
            1 for review in reviews if review.get("constraint_override")
        ),
        "blocked_by_cost_filter": sum(
            1 for review in reviews if review.get("blocked_by_cost_filter")
        ),
        "blocked_by_regime_filter": sum(
            1 for review in reviews if review.get("blocked_by_regime_filter")
        ),
        "short_overrides": sum(
            1 for review in reviews if review.get("constraint_override") == "short_disabled"
        ),
        "exit_policy_overrides": sum(
            1 for review in reviews if review.get("exit_policy_override")
        ),
        "agent_close_delayed_count": sum(
            1
            for review in reviews
            if review.get("exit_policy_override") == "agent_close_delayed"
        ),
        "repeated_entries_avoided": sum(
            1
            for review in reviews
            if review["postprocessing_action"] == "stateful_override_hold"
        ),
        "postprocessor_fallbacks": sum(
            1 for review in reviews if review["postprocessing_action"] == "fallback_no_trade"
        ),
        "active_decisions_before_postprocessing": sum(
            1
            for review in reviews
            if review["decision_before_postprocessing"] in {"LONG", "SHORT"}
        ),
        "active_decisions_after_constraints": sum(
            1 for review in reviews if review.get("decision_after_constraints") in {"LONG", "SHORT"}
        ),
        "close_raw_count": sum(1 for review in reviews if review.get("raw_decision") == "CLOSE"),
        "close_after_constraints_count": sum(
            1 for review in reviews if review.get("decision_after_constraints") == "CLOSE"
        ),
        "active_decisions_after_postprocessing": sum(
            1 for review in reviews if review["decision"] in {"LONG", "SHORT"}
        ),
        "trades": len(trades),
        "positions_open": len(broker.positions),
        "positions_closed": len(trades),
        "force_closed_count": sum(
            1
            for trade in closed_trades_ledger
            if trade.get("exit_reason") == "evaluation_window_end"
        ),
        "paper_open_position_events": sum(
            1 for review in reviews if review["execution_event"].get("action") == "OPEN_POSITION"
        ),
        "realized_pnl": official_pnl,
        "unrealized_pnl": unrealized_pnl,
        "final_equity_pnl": final_equity_pnl,
        "final_equity_pnl_per_trade": final_equity_pnl / trade_count if trade_count else 0.0,
        "final_equity_pnl_per_window": final_equity_pnl,
        "pnl": official_pnl,
        "fees": sum(float(trade.get("fees") or 0.0) for trade in trades),
        "slippage": sum(float(trade.get("slippage") or 0.0) for trade in trades),
        "agreement_rate_with_baseline": _rate(
            sum(1 for review in reviews if review["decision"] == review["baseline_decision"]),
            len(reviews),
        ),
        "override_rate": _rate(
            sum(1 for review in reviews if review["decision"] != review["baseline_decision"]),
            len(reviews),
        ),
        "trades_avoided": baseline_active - validated,
        **baseline_outcomes,
        "average_duration_seconds": (
            sum(float(review["provider_duration_seconds"]) for review in reviews) / len(reviews)
            if reviews
            else 0.0
        ),
        "reasons": _reason_categories(reviews),
        "active_decisions_blocked": _active_decisions_blocked(reviews),
        "management_decisions_when_position_open": sum(
            1
            for review in reviews
            if review["portfolio_before_decision"].get("has_open_position")
            and review["decision"] in {"HOLD", "CLOSE", "NO_TRADE"}
        ),
        "validation_rate_when_no_position": _rate(
            sum(
                1
                for review in reviews
                if not review["portfolio_before_decision"].get("has_open_position")
                and review["decision"] in {"LONG", "SHORT"}
            ),
            sum(
                1
                for review in reviews
                if not review["portfolio_before_decision"].get("has_open_position")
            ),
        ),
        "reviews": reviews,
        "decision_cache": _decision_cache_summary(reviews),
        "closed_trades_ledger": closed_trades_ledger,
        "position_events": position_events,
        "ledger_pnl_matches_official": abs(ledger_pnl - official_pnl) <= 1e-6,
        "ledger_pnl_delta": ledger_pnl - official_pnl,
        "ledger_pnl": ledger_pnl,
        "ledger_trade_count": len(closed_trades_ledger),
        "safety": "Le systeme V1.8C.9 ne peut toujours pas passer d'ordre reel.",
    }


def _reason_categories(reviews):
    counts = Counter()
    for review in reviews:
        text = str(review.get("raw_response") or "").lower()
        if "insuffisant" in text or "unclear" in text or "no clear" in text:
            counts["signal insuffisant"] += 1
        if "derivative" in text or "funding" in text or "open interest" in text:
            counts["donnees derivees indisponibles"] += 1
        if "trend" in text or "tendance" in text:
            counts["tendance non claire"] += 1
        if "risk/reward" in text or "risque" in text:
            counts["ratio risque/rendement insuffisant"] += 1
    return dict(counts)


def _decision_cache_summary(reviews):
    statuses = Counter(review.get("decision_cache_status") for review in reviews)
    return {
        "enabled": any(review.get("decision_cache_status") != "disabled" for review in reviews),
        "hits": statuses.get("hit", 0),
        "external_hits": statuses.get("external_hit", 0),
        "misses": statuses.get("miss", 0),
        "written": statuses.get("written", 0),
        "readonly_misses": sum(
            1
            for review in reviews
            if str(review.get("provider_error") or "").startswith("decision_cache_miss_readonly")
        ),
        "statuses": dict(statuses),
    }


def _apply_variant_filters(decision, *, decision_context_payload, filter_config):
    result = {
        "decision": decision,
        "action": "none",
        "blocked_by_cost_filter": False,
        "blocked_by_regime_filter": False,
        "cost_ratio": None,
        "regime_reason": None,
    }
    if decision.decision.value not in {"LONG", "SHORT"}:
        return result

    cost_filter = filter_config.get("cost_filter") or {}
    if cost_filter.get("enabled"):
        costs = decision_context_payload.get("costs", {})
        expected_move = costs.get("candidate_expected_move")
        round_trip_cost = costs.get("estimated_round_trip_cost")
        ratio = (
            float(expected_move) / float(round_trip_cost)
            if expected_move and round_trip_cost
            else 0.0
        )
        result["cost_ratio"] = ratio
        threshold = float(cost_filter.get("min_expected_move_to_cost_ratio") or 0.0)
        if ratio < threshold:
            result["decision"] = no_trade_decision(
                decision.profile,
                decision.asset,
                decision.horizon,
                f"Blocked by cost filter: expected_move_to_cost_ratio={ratio:.3f}",
            )
            result["action"] = "cost_filter_block"
            result["blocked_by_cost_filter"] = True
            return result

    regime_filter = filter_config.get("regime_filter") or {}
    if regime_filter.get("enabled"):
        market_regime = decision_context_payload.get("market", {}).get("market_regime") or {}
        trend = str(market_regime.get("trend") or "").lower()
        volatility_regime = str(market_regime.get("volatility_regime") or "").lower()
        blocked_trends = {str(item).lower() for item in regime_filter.get("block_long_trends", [])}
        block_extreme = bool(regime_filter.get("block_extreme_volatility", True))
        if decision.decision.value == "LONG" and trend in blocked_trends:
            result["decision"] = no_trade_decision(
                decision.profile,
                decision.asset,
                decision.horizon,
                f"Blocked by regime filter: trend={trend}",
            )
            result["action"] = "regime_filter_block"
            result["blocked_by_regime_filter"] = True
            result["regime_reason"] = f"trend={trend}"
            return result
        if block_extreme and volatility_regime in {"extreme", "high_volatility_extreme"}:
            result["decision"] = no_trade_decision(
                decision.profile,
                decision.asset,
                decision.horizon,
                f"Blocked by regime filter: volatility_regime={volatility_regime}",
            )
            result["action"] = "regime_filter_block"
            result["blocked_by_regime_filter"] = True
            result["regime_reason"] = f"volatility_regime={volatility_regime}"
            return result

    return result


def _cache_context_hash(*, candidate, portfolio, trade_constraints):
    position = portfolio.get("current_position") or {}
    return stable_json_hash(
        {
            "candidate_id": candidate.candidate_id,
            "decision_timestamp": candidate.decision_timestamp,
            "context_index": candidate.context_index,
            "baseline_policy": candidate.baseline_policy,
            "baseline_decision": candidate.baseline_decision,
            "current_price": round(float(candidate.current_price), 8),
            "has_open_position": bool(portfolio.get("current_position")),
            "position_side": position.get("side"),
            "entry_price": position.get("entry_price"),
            "bars_in_position": portfolio.get("bars_in_position", 0),
            "trade_constraints": trade_constraints,
        }
    )


def _active_decisions_blocked(reviews):
    blocked = []
    for review in reviews:
        was_active = review["decision_before_postprocessing"] in {"LONG", "SHORT"}
        blocked_by_postprocessor = review["postprocessing_action"] == "fallback_no_trade"
        blocked_by_risk = was_active and not review["risk_approved"]
        if not was_active or not (blocked_by_postprocessor or blocked_by_risk):
            continue
        payload = _safe_json(review.get("raw_response"))
        blocked.append(
            {
                "candidate_id": review["candidate"].get("candidate_id"),
                "decision_before_postprocessing": review["decision_before_postprocessing"],
                "final_decision_after_postprocessing": review["decision"],
                "strategy": payload.get("strategy"),
                "critical_data_used": payload.get("critical_data_used", []),
                "missing_critical_data": review.get("postprocessing_missing_required", []),
                "candidate_setup": review["candidate"],
                "reasoning_summary": payload.get("reasoning_summary"),
                "postprocessing_warnings": review.get("postprocessing_warnings", []),
                "risk_rejection_reason": review.get("risk_reasons", []),
                "needed_to_execute": (
                    "Use exact critical_data_used keys required by risk config, including "
                    "price and volatility, with coherent stop/take-profit and risk_fraction."
                ),
            }
        )
    return blocked


def _entry_metadata(candidate, decision_payload, decision_context, context):
    market = decision_context.get("market", {})
    return {
        "candidate_id_entry": candidate.candidate_id,
        "entry_decision": decision_payload,
        "entry_context_hash": decision_context.get("context_hash"),
        "entry_context_index": candidate.context_index,
        "candidate_setup": candidate_to_dict(candidate),
        "setup_quality": decision_payload.get("setup_quality"),
        "setup_quality_score": decision_payload.get("setup_quality_score"),
        "confidence": decision_payload.get("confidence"),
        "risk_fraction": decision_payload.get("risk_fraction"),
        "risk_reward_initial": _risk_reward(
            decision_payload.get("reference_entry_price"),
            decision_payload.get("stop_loss"),
            decision_payload.get("take_profit"),
        ),
        "critical_data_used": decision_payload.get("critical_data_used", []),
        "market_regime_entry": market.get("market_regime"),
        "trend_short_entry": market.get("trend_short"),
        "trend_long_entry": market.get("trend_long"),
        "volatility_entry": market.get("volatility"),
        "derivatives_availability_entry": (
            decision_context.get("derivatives", {}).get("derivatives_availability_summary", {})
        ),
        "entry_market": context.get("market", {}),
    }


def _ledger_entry(
    trade,
    metadata,
    *,
    candidate_id_exit,
    exit_decision,
    exit_context_hash,
    exit_context_index,
):
    entry_index = metadata.get("entry_context_index")
    duration_bars = (
        max(0, int(exit_context_index) - int(entry_index))
        if entry_index is not None and exit_context_index is not None
        else None
    )
    net_pnl = float(trade.get("pnl") or 0.0)
    fees = float(trade.get("fees") or 0.0)
    gross_pnl = net_pnl + fees
    return {
        "trade_id": trade.get("id"),
        "candidate_id_entry": metadata.get("candidate_id_entry"),
        "candidate_id_exit": candidate_id_exit,
        "profile": trade.get("profile"),
        "asset": trade.get("asset"),
        "side": trade.get("side"),
        "strategy": trade.get("strategy"),
        "entry_timestamp": trade.get("entry_timestamp"),
        "entry_price": trade.get("entry_price"),
        "entry_decision": metadata.get("entry_decision"),
        "entry_context_hash": metadata.get("entry_context_hash"),
        "exit_timestamp": trade.get("exit_timestamp"),
        "exit_price": trade.get("exit_price"),
        "exit_reason": trade.get("close_reason") or "other",
        "exit_decision": exit_decision,
        "exit_context_hash": exit_context_hash,
        "size": trade.get("size"),
        "gross_pnl": gross_pnl,
        "fees": fees,
        "slippage": trade.get("slippage"),
        "net_pnl": net_pnl,
        "net_pnl_percent": trade.get("pnl_percent"),
        "duration_bars": duration_bars,
        "duration_hours": duration_bars * 4 if duration_bars is not None else None,
        "setup_quality": metadata.get("setup_quality"),
        "setup_quality_score": metadata.get("setup_quality_score"),
        "confidence": metadata.get("confidence"),
        "risk_fraction": metadata.get("risk_fraction"),
        "risk_reward_initial": metadata.get("risk_reward_initial"),
        "critical_data_used": metadata.get("critical_data_used", []),
        "candidate_setup": metadata.get("candidate_setup"),
        "market_regime_entry": metadata.get("market_regime_entry"),
        "trend_short_entry": metadata.get("trend_short_entry"),
        "trend_long_entry": metadata.get("trend_long_entry"),
        "volatility_entry": metadata.get("volatility_entry"),
        "derivatives_availability_entry": metadata.get("derivatives_availability_entry"),
    }


def _position_event(
    *,
    timestamp,
    candidate_id,
    event_type,
    position_id,
    decision,
    price,
    reason,
    fees,
    slippage,
    pnl_delta,
):
    return {
        "timestamp": timestamp,
        "candidate_id": candidate_id,
        "event_type": event_type,
        "position_id": position_id,
        "decision": decision,
        "price": price,
        "reason": reason,
        "fees": fees,
        "slippage": slippage,
        "pnl_delta": pnl_delta,
    }


def _risk_reward(entry, stop, take):
    if not entry or not stop or not take:
        return None
    risk = abs(float(entry) - float(stop))
    reward = abs(float(take) - float(entry))
    return reward / risk if risk else None


def _top_enum_violations(reviews):
    counter = Counter()
    for review in reviews:
        for violation in review.get("enum_violations") or []:
            key = f"{violation.get('field_name')}={violation.get('invalid_value')}"
            counter[key] += 1
    return dict(counter.most_common(10))


def _setup_quality_distribution(reviews):
    counter = Counter()
    for review in reviews:
        payload = _safe_json(review.get("raw_response"))
        value = payload.get("setup_quality")
        if value is None and review["parser_validity"] != "parser_fallback":
            value = "missing"
        if value is not None:
            counter[str(value)] += 1
    return dict(counter)


def _setup_quality_score_average(reviews):
    scores = []
    for review in reviews:
        payload = _safe_json(review.get("raw_response"))
        value = payload.get("setup_quality_score")
        if isinstance(value, int | float):
            scores.append(float(value))
    return sum(scores) / len(scores) if scores else None


def _safe_json(raw):
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _outcome_comparison(candidates, reviews, data):
    baseline_results = [
        _estimate_candidate_outcome(candidate, data)
        for candidate in candidates
        if candidate.baseline_decision in {"LONG", "SHORT"}
    ]
    validated_indexes = {
        index
        for index, review in enumerate(reviews)
        if review["decision"] == review["baseline_decision"]
        and review["decision"] in {"LONG", "SHORT"}
    }
    executable_indexes = {
        index
        for index, review in enumerate(reviews)
        if index in validated_indexes and bool(review["risk_approved"])
    }
    validated_results = [
        result for index, result in enumerate(baseline_results) if index in validated_indexes
    ]
    executable_results = [
        result for index, result in enumerate(baseline_results) if index in executable_indexes
    ]
    filtered_results = [
        result for index, result in enumerate(baseline_results) if index not in executable_indexes
    ]
    return {
        "baseline_brut_outcome": _summarize_outcomes(baseline_results),
        "gpt_validated_pre_risk_outcome": _summarize_outcomes(validated_results),
        "gpt_executable_outcome": _summarize_outcomes(executable_results),
        "filtered_baseline_outcome": _summarize_outcomes(filtered_results),
        "winning_trades_missed": sum(1 for item in filtered_results if item["pnl_percent"] > 0),
        "losing_trades_filtered": sum(1 for item in filtered_results if item["pnl_percent"] < 0),
    }


def _estimate_candidate_outcome(candidate, data, lookahead_bars: int = 12):
    entry = float(candidate.current_price)
    stop = candidate.suggested_stop_loss
    take = candidate.suggested_take_profit
    start = int(candidate.context_index) + 1
    end = min(start + lookahead_bars, len(data))
    exit_price = float(data["close"].iloc[min(end, len(data)) - 1])
    close_reason = "lookahead_end"
    for _, candle in data.iloc[start:end].iterrows():
        high = float(candle["high"])
        low = float(candle["low"])
        if candidate.baseline_decision == "LONG":
            if stop is not None and low <= float(stop):
                exit_price = float(stop)
                close_reason = "stop_loss"
                break
            if take is not None and high >= float(take):
                exit_price = float(take)
                close_reason = "take_profit"
                break
        if candidate.baseline_decision == "SHORT":
            if stop is not None and high >= float(stop):
                exit_price = float(stop)
                close_reason = "stop_loss"
                break
            if take is not None and low <= float(take):
                exit_price = float(take)
                close_reason = "take_profit"
                break
    if candidate.baseline_decision == "LONG":
        pnl_percent = (exit_price - entry) / entry if entry else 0.0
    else:
        pnl_percent = (entry - exit_price) / entry if entry else 0.0
    return {
        "candidate_id": candidate.candidate_id,
        "baseline_policy": candidate.baseline_policy,
        "side": candidate.baseline_decision,
        "entry": entry,
        "exit": exit_price,
        "close_reason": close_reason,
        "pnl_percent": pnl_percent,
    }


def _summarize_outcomes(outcomes):
    total = sum(float(item["pnl_percent"]) for item in outcomes)
    wins = sum(1 for item in outcomes if float(item["pnl_percent"]) > 0)
    losses = sum(1 for item in outcomes if float(item["pnl_percent"]) < 0)
    return {
        "count": len(outcomes),
        "wins": wins,
        "losses": losses,
        "total_pnl_percent": total,
        "average_pnl_percent": total / len(outcomes) if outcomes else 0.0,
    }


def _rate(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def _markdown(report):
    return "\n".join(
        [
            "# Codex setup review V1.8C.9",
            "",
            f"- Candidats trouves : {report['candidates_found']}",
            f"- Candidats soumis : {report['candidates_submitted']}",
            f"- JSON valid rate : {report['json_valid_rate']}",
            f"- Raw JSON valid rate : {report['raw_json_valid_rate']}",
            f"- Repaired JSON count : {report['repaired_json_count']}",
            f"- Final parse success rate : {report['final_parse_success_rate']}",
            f"- Strict parser fallback count : {report['strict_parser_fallback_count']}",
            f"- Enum violations count : {report['enum_violations_count']}",
            f"- Top enum violations : {report['top_enum_violations']}",
            f"- Setup quality distribution : {report['setup_quality_distribution']}",
            f"- Setup quality score average : {report['setup_quality_score_average']}",
            f"- Distribution decisions : {report['decision_distribution']}",
            f"- Distribution decisions brutes : {report['raw_decision_distribution']}",
            (
                "- Distribution apres contraintes : "
                f"{report['decision_after_constraints_distribution']}"
            ),
            (
                "- Distribution apres exit policy : "
                f"{report['decision_after_exit_policy_distribution']}"
            ),
            f"- Validation rate : {report['validation_rate']}",
            f"- Refusal rate : {report['refusal_rate']}",
            f"- Risk rejects : {report['risk_rejects']}",
            f"- HOLD count : {report['hold_count']}",
            f"- CLOSE count : {report['close_count']}",
            f"- Stateful overrides : {report['stateful_overrides']}",
            f"- Constraint overrides : {report['constraint_overrides']}",
            f"- SHORT overrides : {report['short_overrides']}",
            f"- Exit policy overrides : {report['exit_policy_overrides']}",
            f"- CLOSE delayed count : {report['agent_close_delayed_count']}",
            f"- Repeated entries avoided : {report['repeated_entries_avoided']}",
            f"- Postprocessor fallbacks : {report['postprocessor_fallbacks']}",
            (
                "- Decisions actives avant/apres postprocessing/apres contraintes : "
                f"{report['active_decisions_before_postprocessing']} / "
                f"{report['active_decisions_after_postprocessing']} / "
                f"{report['active_decisions_after_constraints']}"
            ),
            f"- Trades : {report['trades']}",
            f"- Positions paper ouvertes : {report['paper_open_position_events']}",
            f"- Positions ouvertes fin run : {report['positions_open']}",
            f"- Positions fermees : {report['positions_closed']}",
            f"- Realized PnL : {report['realized_pnl']}",
            f"- Unrealized PnL : {report['unrealized_pnl']}",
            f"- Final equity PnL : {report['final_equity_pnl']}",
            f"- Force closed count : {report['force_closed_count']}",
            f"- PnL : {report['pnl']}",
            f"- Fees : {report['fees']}",
            f"- Slippage : {report['slippage']}",
            f"- Ledger trades : {report['ledger_trade_count']}",
            f"- Ledger PnL : {report['ledger_pnl']}",
            f"- Ledger PnL delta : {report['ledger_pnl_delta']}",
            f"- Ledger matches official : {report['ledger_pnl_matches_official']}",
            f"- Agreement baseline : {report['agreement_rate_with_baseline']}",
            f"- Override rate : {report['override_rate']}",
            f"- Duree moyenne : {report['average_duration_seconds']:.3f}s",
            "",
            "## Baseline brute vs GPT-5.5 setup review",
            "",
            f"- Baseline brute estimee : {report['baseline_brut_outcome']}",
            (
                "- Setups valides par GPT avant risk engine : "
                f"{report['gpt_validated_pre_risk_outcome']}"
            ),
            f"- Setups executables apres risk engine : {report['gpt_executable_outcome']}",
            f"- Trades gagnants rates : {report['winning_trades_missed']}",
            f"- Trades perdants filtres : {report['losing_trades_filtered']}",
            "",
            "## Raisons",
            "",
            json.dumps(report["reasons"], indent=2, ensure_ascii=False),
            "",
            "## Active decisions blocked by risk engine",
            "",
            json.dumps(report["active_decisions_blocked"], indent=2, ensure_ascii=False),
            "",
            "## Limites",
            "",
            (
                "Echantillon trop petit pour conclure. Ce test evalue le filtrage de "
                "setups candidats, pas une profitabilite."
            ),
            report["safety"],
        ]
    )


def _with_candle_times(data, profile):
    enriched = data.copy()
    enriched["candle_open_timestamp"] = enriched["timestamp"]
    enriched["candle_close_timestamp"] = enriched["candle_open_timestamp"].apply(
        lambda timestamp: candle_close_time(timestamp, profile["timeframe"])
    )
    enriched["available_at_utc"] = enriched["candle_close_timestamp"]
    return enriched


def _portfolio_from_broker(broker, profile, *, current_price: float, timestamp: str):
    positions = [
        position
        for position in broker.positions.values()
        if position.profile == profile["name"] and position.asset == profile["symbol"]
    ]
    current_position = positions[0] if positions else None
    position_payload = asdict(current_position) if current_position else None
    unrealized = _position_pnl(current_position, current_price) if current_position else 0.0
    notional = (
        current_position.entry_price * current_position.size
        if current_position is not None
        else 0.0
    )
    return {
        "open_positions": [asdict(position) for position in positions],
        "current_position": position_payload,
        "current_price": current_price,
        "timestamp": timestamp,
        "bars_in_position": _bars_in_position(current_position, timestamp),
        "unrealized_pnl": unrealized,
        "unrealized_pnl_percent": unrealized / notional if notional else 0.0,
    }


def _position_pnl(position, price: float) -> float:
    if position is None:
        return 0.0
    if position.side == "LONG":
        return (price - position.entry_price) * position.size
    return (position.entry_price - price) * position.size


def _bars_in_position(position, timestamp: str) -> int:
    if position is None:
        return 0
    import pandas as pd

    entered = pd.Timestamp(position.entry_timestamp)
    current = pd.Timestamp(timestamp)
    return max(0, int((current - entered) / pd.Timedelta(hours=4)))


def _last_price(data) -> float:
    return float(data["close"].iloc[-1]) if len(data) else 0.0


if __name__ == "__main__":
    main()
