from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def analyze_codex_cli_decisions(
    result: dict[str, Any],
    offline: dict[str, Any] | None = None,
    breakout: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decisions = result.get("decisions", [])
    codex_decisions = [
        decision for decision in decisions if decision.get("provider_name") == "codex_cli"
    ]
    valid_json = sum(
        1 for decision in codex_decisions if decision.get("parser_validity") == "valid_schema"
    )
    durations = [
        float(decision.get("provider_duration_seconds") or 0.0)
        for decision in codex_decisions
        if decision.get("provider_duration_seconds") is not None
    ]
    payloads = [_safe_payload(decision.get("raw_response")) for decision in codex_decisions]
    confidence = [float(payload.get("confidence") or 0.0) for payload in payloads if payload]
    risk_fraction = [float(payload.get("risk_fraction") or 0.0) for payload in payloads if payload]
    distribution = Counter(decision.get("decision", "unknown") for decision in codex_decisions)
    setup_quality_distribution = Counter(
        str(payload.get("setup_quality") or "unknown") for payload in payloads if payload
    )
    fallback_count = sum(
        1
        for decision in codex_decisions
        if decision.get("provider_error")
        or decision.get("parser_validity") != "valid_schema"
        or decision.get("decision_validity") not in {None, "valid_schema"}
    )
    timeout_count = sum(
        1
        for decision in codex_decisions
        if "timed out" in str(decision.get("provider_error") or "").lower()
    )
    failures = [
        {
            "timestamp": decision.get("timestamp"),
            "error": decision.get("provider_error"),
            "parser_validity": decision.get("parser_validity"),
            "decision_validity": decision.get("decision_validity"),
        }
        for decision in codex_decisions
        if decision.get("provider_error") or decision.get("parser_validity") != "valid_schema"
    ]
    total = len(codex_decisions)
    offline_decisions = (offline or {}).get("decisions", [])
    agreement = _decision_agreement(codex_decisions, offline_decisions)
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "provider": "codex_cli",
        "model": _first(codex_decisions, "provider_model"),
        "reasoning_effort": _first(codex_decisions, "provider_reasoning_effort"),
        "total_codex_cli_calls": total,
        "valid_json_count": valid_json,
        "invalid_json_count": max(0, total - valid_json),
        "valid_json_rate": valid_json / total if total else 0.0,
        "min_duration_seconds": min(durations) if durations else 0.0,
        "average_duration_seconds": sum(durations) / len(durations) if durations else 0.0,
        "max_duration_seconds": max(durations) if durations else 0.0,
        "timeout_count": timeout_count,
        "fallback_count": fallback_count,
        "decision_distribution": dict(distribution),
        "active_decision_rate": (
            sum(distribution.get(key, 0) for key in ["LONG", "SHORT", "CLOSE"]) / total
            if total
            else 0.0
        ),
        "no_trade_rate": distribution.get("NO_TRADE", 0) / total if total else 0.0,
        "average_confidence": sum(confidence) / len(confidence) if confidence else 0.0,
        "average_risk_fraction": sum(risk_fraction) / len(risk_fraction) if risk_fraction else 0.0,
        "setup_quality_distribution": dict(setup_quality_distribution),
        "reasons_for_active_trades": _active_trade_reasons(payloads),
        "top_reasoning_categories": _classify_reasoning(payloads),
        "top_reasoning_summaries": _top_reasoning_summaries(payloads),
        "risk_rejects": sum(
            1 for decision in codex_decisions if not decision.get("risk_approved", True)
        ),
        "failures": failures,
        "raw_response_examples": [
            {
                "timestamp": decision.get("timestamp"),
                "context_hash": decision.get("context_hash"),
                "prompt_hash": decision.get("prompt_hash"),
                "raw_response": _redact(decision.get("raw_response", "")),
            }
            for decision in codex_decisions[:5]
        ],
        "valid_json_examples": [
            {
                "timestamp": decision.get("timestamp"),
                "raw_response": _redact(decision.get("raw_response", "")),
            }
            for decision in codex_decisions
            if decision.get("parser_validity") == "valid_schema"
        ][:5],
        "fallback_examples": failures[:5],
        "decision_agreement_vs_offline_conservative": agreement,
        "metrics": result.get("metrics", {}),
        "offline_conservative_metrics": (offline or {}).get("metrics", {}),
        "state_aware_breakout_metrics": (breakout or {}).get("metrics", {}),
        "prudent_scores": {
            "codex_cli": _prudent_score(result.get("metrics", {})),
            "llm_offline_conservative": _prudent_score((offline or {}).get("metrics", {})),
            "state_aware_breakout": _prudent_score((breakout or {}).get("metrics", {})),
        },
    }


def write_codex_cli_sample_report(
    *,
    result: dict[str, Any],
    offline_comparison: dict[str, Any],
    breakout_comparison: dict[str, Any] | None = None,
    output_dir: Path,
    version: str,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis = analyze_codex_cli_decisions(result, offline_comparison, breakout_comparison)
    suffix = _version_suffix(version)
    md_path = output_dir / f"codex_cli_sample_backtest_{suffix}.md"
    json_path = output_dir / f"codex_cli_sample_backtest_{suffix}.json"
    analysis["version"] = version
    analysis["run_id"] = result.get("run_id")
    analysis["offline_run_id"] = offline_comparison.get("run_id")
    analysis["breakout_run_id"] = (breakout_comparison or {}).get("run_id")
    json_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(analysis), encoding="utf-8")
    return {"markdown": str(md_path), "json": str(json_path)}


def write_codex_cli_decision_report(
    analysis: dict[str, Any],
    output_dir: Path,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    version = str(analysis.get("version") or "V1.8C")
    suffix = _version_suffix(version)
    md_path = output_dir / f"codex_cli_decisions_{suffix}.md"
    json_path = output_dir / f"codex_cli_decisions_{suffix}.json"
    json_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(analysis), encoding="utf-8")
    return {"markdown": str(md_path), "json": str(json_path)}


def _markdown(analysis: dict[str, Any]) -> str:
    lines = [
        f"# Rapport Codex CLI {analysis.get('version', 'V1.8C')}",
        "",
        f"- Genere le UTC : {analysis.get('generated_at_utc')}",
        f"- Provider : {analysis.get('provider')}",
        f"- Modele : {analysis.get('model')}",
        f"- Reasoning effort : {analysis.get('reasoning_effort')}",
        f"- Appels Codex CLI : {analysis.get('total_codex_cli_calls')}",
        f"- JSON valides : {analysis.get('valid_json_count')}",
        f"- JSON invalides : {analysis.get('invalid_json_count')}",
        f"- Timeouts : {analysis.get('timeout_count', 0)}",
        f"- Fallbacks : {analysis.get('fallback_count', 0)}",
        f"- Duree min/moyenne/max : {analysis.get('min_duration_seconds', 0.0):.3f}s / "
        f"{analysis.get('average_duration_seconds', 0.0):.3f}s / "
        f"{analysis.get('max_duration_seconds', 0.0):.3f}s",
        f"- Duree moyenne : {analysis.get('average_duration_seconds'):.3f}s",
        "",
        "## Distribution des decisions",
        "",
        json.dumps(analysis.get("decision_distribution", {}), indent=2, ensure_ascii=False),
        "",
        "## Distribution setup_quality",
        "",
        json.dumps(analysis.get("setup_quality_distribution", {}), indent=2, ensure_ascii=False),
        "",
        "## Metriques",
        "",
        json.dumps(analysis.get("metrics", {}), indent=2, ensure_ascii=False),
        "",
        "## Comparaison llm_offline_conservative",
        "",
        json.dumps(analysis.get("offline_conservative_metrics", {}), indent=2, ensure_ascii=False),
        "",
        "## Comparaison state_aware_breakout",
        "",
        json.dumps(analysis.get("state_aware_breakout_metrics", {}), indent=2, ensure_ascii=False),
        "",
        "## Score prudent",
        "",
        json.dumps(analysis.get("prudent_scores", {}), indent=2, ensure_ascii=False),
        "",
        "## Pourquoi GPT-5.5 refuse de trader ?",
        "",
        json.dumps(analysis.get("top_reasoning_categories", {}), indent=2, ensure_ascii=False),
        "",
        _no_trade_conclusion(analysis),
        "",
        "## Echecs et fallbacks",
        "",
        json.dumps(analysis.get("failures", []), indent=2, ensure_ascii=False),
        "",
        "## Limites",
        "",
        "- Echantillon volontairement tres court.",
        "- Ce test valide l'integration Codex CLI, pas une profitabilite.",
        (
            f"- Le systeme {analysis.get('version', 'V1.8C')} ne peut toujours pas passer "
            "d'ordre reel."
        ),
    ]
    return "\n".join(lines) + "\n"


def _safe_payload(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def _first(decisions: list[dict[str, Any]], key: str) -> Any:
    for decision in decisions:
        if decision.get(key) is not None:
            return decision[key]
    return None


def _redact(text: str) -> str:
    return text[:1000]


def _version_suffix(version: str) -> str:
    if version == "V1.8C.2":
        return "v1_8C_2"
    if version == "V1.8C.1":
        return "v1_8C_1"
    return "v1_8C"


def _classify_reasoning(payloads: list[dict[str, Any]]) -> dict[str, int]:
    categories = Counter()
    for payload in payloads:
        text = str(payload.get("reasoning_summary") or "").lower()
        critical = " ".join(str(item).lower() for item in payload.get("critical_data_used", []))
        combined = f"{text} {critical}"
        if any(term in combined for term in ["unclear", "insuffisant", "no clear", "edge"]):
            categories["signal insuffisant"] += 1
        if any(term in combined for term in ["derivative", "funding", "open interest", "basis"]):
            categories["donnees derivees indisponibles"] += 1
        if any(term in combined for term in ["volatility", "volatilite", "volatilité"]):
            categories["volatilite defavorable ou indisponible"] += 1
        if any(term in combined for term in ["trend", "tendance", "unknown"]):
            categories["tendance non claire"] += 1
        if any(term in combined for term in ["risk/reward", "rendement", "risk ratio"]):
            categories["ratio risque/rendement insuffisant"] += 1
        no_position = any(
            term in combined
            for term in ["no open position", "aucune position ouverte", "has_open_position:false"]
        )
        if not no_position and any(
            term in combined
            for term in [
                "existing position",
                "position already",
                "position deja",
                "position déjà",
            ]
        ):
            categories["position deja ouverte"] += 1
        if not categories:
            categories["autre"] += 1
    return dict(categories)


def _top_reasoning_summaries(payloads: list[dict[str, Any]], limit: int = 10) -> list[str]:
    summaries = [
        str(payload.get("reasoning_summary"))
        for payload in payloads
        if payload.get("reasoning_summary")
    ]
    return [summary for summary, _count in Counter(summaries).most_common(limit)]


def _active_trade_reasons(payloads: list[dict[str, Any]]) -> list[str]:
    reasons = []
    for payload in payloads:
        if payload.get("decision") in {"LONG", "SHORT", "CLOSE"}:
            reasons.append(str(payload.get("why_not_no_trade") or payload.get("reasoning_summary")))
    return reasons[:10]


def _decision_agreement(
    codex_decisions: list[dict[str, Any]],
    offline_decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    pairs = list(zip(codex_decisions, offline_decisions, strict=False))
    if not pairs:
        return {"count": 0, "matches": 0, "agreement_rate": 0.0}
    matches = sum(1 for left, right in pairs if left.get("decision") == right.get("decision"))
    return {"count": len(pairs), "matches": matches, "agreement_rate": matches / len(pairs)}


def _prudent_score(metrics: dict[str, Any]) -> float:
    return (
        float(metrics.get("realized_pnl_per_day") or 0.0)
        - abs(float(metrics.get("max_drawdown") or 0.0)) * 100
        - float(metrics.get("fees_per_day") or 0.0) * 0.1
        - float(metrics.get("slippage_per_day") or 0.0) * 0.1
        - float(metrics.get("risk_rejected_per_day") or 0.0) * 2
    )


def _no_trade_conclusion(analysis: dict[str, Any]) -> str:
    distribution = analysis.get("decision_distribution", {})
    total = int(analysis.get("total_codex_cli_calls") or 0)
    if total and distribution.get("NO_TRADE") == total:
        return (
            "GPT-5.5 a repondu uniquement NO_TRADE sur cet echantillon. Le comportement est tres "
            "conservateur, favorable a la securite, mais il peut necessiter un prompt moins "
            "restrictif plus tard. Il ne faut pas assouplir avant davantage d'echantillons."
        )
    return "GPT-5.5 n'a pas repondu uniquement NO_TRADE sur cet echantillon."
