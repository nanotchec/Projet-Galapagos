from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from galapagos.journal.sqlite_store import SQLiteStore


def generate_llm_decisions_report(
    store: SQLiteStore,
    output_dir: str | Path,
    *,
    report_date: date | None = None,
) -> dict[str, Path]:
    report_date = report_date or datetime.now(UTC).date()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = [dict(row) for row in store.query("SELECT * FROM agent_decisions ORDER BY id")]
    summary = summarize_llm_decisions(rows)
    summary["date"] = report_date.isoformat()
    md_path = output / f"llm_decisions_{report_date.isoformat()}.md"
    json_path = output / f"llm_decisions_{report_date.isoformat()}.json"
    md_path.write_text(_markdown(summary), encoding="utf-8")
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}


def summarize_llm_decisions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    validity_counts = Counter(row.get("decision_validity") for row in rows)
    decision_counts: Counter[str] = Counter()
    confidences: list[float] = []
    risk_rejected = 0
    reasons: Counter[str] = Counter()
    invalid_examples: list[dict[str, Any]] = []
    for row in rows:
        parsed = _loads(row.get("parsed_decision"))
        decision = parsed.get("decision", "unknown")
        decision_counts[decision] += 1
        if isinstance(parsed.get("confidence"), int | float):
            confidences.append(float(parsed["confidence"]))
        risk = _loads(row.get("risk_engine_result"))
        if risk and not risk.get("approved", True):
            risk_rejected += 1
            reasons.update(risk.get("reasons", []))
        if row.get("decision_validity") != "valid_schema" and len(invalid_examples) < 5:
            invalid_examples.append(
                {
                    "id": row.get("id"),
                    "profile": row.get("profile"),
                    "validity": row.get("decision_validity"),
                    "raw_llm_response": row.get("raw_llm_response"),
                }
            )
    total = len(rows)
    return {
        "decision_count": total,
        "valid_schema": validity_counts.get("valid_schema", 0),
        "provider_failure_fallback": validity_counts.get("provider_failure_fallback", 0),
        "parser_fallback": validity_counts.get("parser_fallback", 0),
        "decisions_by_type": dict(decision_counts),
        "average_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "risk_rejected_count": risk_rejected,
        "frequent_rejection_reasons": reasons.most_common(10),
        "invalid_raw_response_examples": invalid_examples,
        "no_trade_rate": decision_counts.get("NO_TRADE", 0) / total if total else 0.0,
    }


def _markdown(summary: dict[str, Any]) -> str:
    return f"""# Rapport decisions LLM - {summary["date"]}

- Nombre de decisions: {summary["decision_count"]}
- valid_schema: {summary["valid_schema"]}
- provider_failure_fallback: {summary["provider_failure_fallback"]}
- parser_fallback: {summary["parser_fallback"]}
- Decisions par type: {summary["decisions_by_type"]}
- Confiance moyenne: {summary["average_confidence"]}
- Decisions refusees par risk engine: {summary["risk_rejected_count"]}
- Raisons frequentes de refus: {summary["frequent_rejection_reasons"]}
- Taux NO_TRADE: {summary["no_trade_rate"]}

## Exemples raw invalides
{_format_invalid_examples(summary["invalid_raw_response_examples"])}
"""


def _format_invalid_examples(examples: list[dict[str, Any]]) -> str:
    if not examples:
        return "- Aucun"
    return "\n".join(
        f"- id={item.get('id')} profile={item.get('profile')} validity={item.get('validity')}: "
        f"{item.get('raw_llm_response')}"
        for item in examples
    )


def _loads(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}

