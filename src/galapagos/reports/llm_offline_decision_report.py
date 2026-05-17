from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def analyze_llm_offline_decisions(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_policy: dict[str, Counter] = defaultdict(Counter)
    confidence: dict[str, list[float]] = defaultdict(list)
    risk_fraction: dict[str, list[float]] = defaultdict(list)
    strategy: dict[str, Counter] = defaultdict(Counter)
    risk_reasons: Counter[str] = Counter()
    raw_examples: list[dict[str, Any]] = []
    fallbacks: list[dict[str, Any]] = []
    for result in results:
        policy = result.get("policy", "unknown")
        if not str(policy).startswith("llm_offline"):
            continue
        for raw in result.get("raw_results", {}).values():
            for decision in raw.get("decisions", []):
                decision_type = decision.get("decision")
                by_policy[policy][decision_type] += 1
                parsed = _raw_payload(decision.get("raw_response"))
                if parsed:
                    confidence[policy].append(float(parsed.get("confidence") or 0.0))
                    risk_fraction[policy].append(float(parsed.get("risk_fraction") or 0.0))
                    strategy[policy][parsed.get("strategy", "unknown")] += 1
                for reason in decision.get("risk_reasons") or []:
                    risk_reasons[reason] += 1
                if decision.get("raw_response") and len(raw_examples) < 10:
                    raw_examples.append(
                        {
                            "policy": policy,
                            "context_hash": decision.get("context_hash"),
                            "prompt_hash": decision.get("prompt_hash"),
                            "raw_response": decision.get("raw_response"),
                        }
                    )
                if decision.get("decision_validity") not in {None, "valid_schema"}:
                    fallbacks.append(
                        {
                            "policy": policy,
                            "validity": decision.get("decision_validity"),
                            "reasons": decision.get("context_validation_reasons"),
                            "context_hash": decision.get("context_hash"),
                        }
                    )
    return {
        "decision_distribution_by_policy": {key: dict(value) for key, value in by_policy.items()},
        "average_confidence_by_policy": {
            key: _avg(values) for key, values in confidence.items()
        },
        "average_risk_fraction_by_policy": {
            key: _avg(values) for key, values in risk_fraction.items()
        },
        "strategy_distribution_by_policy": {
            key: dict(value) for key, value in strategy.items()
        },
        "risk_rejection_reasons": dict(risk_reasons),
        "raw_response_examples": raw_examples,
        "fallback_examples": fallbacks[:10],
        "fallback_count": len(fallbacks),
    }


def write_llm_offline_decision_report(
    analysis: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    md_path = output / "llm_offline_decisions_v1_7.md"
    json_path = output / "llm_offline_decisions_v1_7.json"
    md_path.write_text(_markdown(analysis), encoding="utf-8")
    json_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}


def _markdown(analysis: dict[str, Any]) -> str:
    lines = ["# Decisions LLM offline V1.7", ""]
    lines.append("## Distribution des decisions")
    for policy, counts in analysis["decision_distribution_by_policy"].items():
        lines.append(f"### {policy}")
        total = sum(counts.values()) or 1
        for decision, count in counts.items():
            lines.append(f"- {decision}: {count} ({count / total:.2%})")
    lines.extend(["", "## Confiance et risque moyens"])
    for policy, value in analysis["average_confidence_by_policy"].items():
        risk = analysis["average_risk_fraction_by_policy"].get(policy, 0.0)
        lines.append(f"- {policy}: confidence={value:.4f}, risk_fraction={risk:.4f}")
    lines.extend(["", "## Strategies choisies"])
    for policy, counts in analysis["strategy_distribution_by_policy"].items():
        lines.append(f"- {policy}: {counts}")
    lines.extend(["", "## Raisons de refus risk engine"])
    for reason, count in analysis["risk_rejection_reasons"].items():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Exemples raw_response"])
    for example in analysis["raw_response_examples"][:5]:
        lines.append(
            f"- {example['policy']} | {example['context_hash']} | "
            f"{example['raw_response']}"
        )
    lines.extend(["", "## Fallbacks parser/validator"])
    lines.append(f"- Nombre: {analysis['fallback_count']}")
    return "\n".join(lines)


def _raw_payload(raw_response: str | None) -> dict[str, Any] | None:
    if not raw_response:
        return None
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        return None


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
