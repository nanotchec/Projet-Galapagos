from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def analyze_parser_fallbacks(report_path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    fallbacks = [
        _fallback_item(review)
        for review in payload.get("reviews", [])
        if review.get("parser_validity") == "parser_fallback"
    ]
    causes = Counter(item["probable_cause"] for item in fallbacks)
    enum_violations = [
        violation
        for item in fallbacks
        for violation in item.get("enum_violations", [])
    ]
    return {
        "version": "V1.8C.7",
        "source_report": str(report_path),
        "total_reviews": len(payload.get("reviews", [])),
        "parser_fallback_count": len(fallbacks),
        "causes": dict(causes),
        "enum_violations_count": len(enum_violations),
        "enum_violations": enum_violations,
        "top_invalid_enum_values": _top_invalid_enum_values(enum_violations),
        "enum_violations_by_field": _enum_violations_by_field(enum_violations),
        "fallbacks": fallbacks,
        "recommendations": _recommendations(causes),
    }


def write_parser_fallback_report(
    analysis: dict[str, Any],
    *,
    output_dir: str | Path = "reports/diagnostics",
) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "parser_fallbacks_v1_8C_7.json"
    md_path = output / "parser_fallbacks_v1_8C_7.md"
    json_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(analysis), encoding="utf-8")
    return md_path, json_path


def _fallback_item(review: dict[str, Any]) -> dict[str, Any]:
    raw = str(review.get("raw_response") or "")
    enum_violations = [
        {
            **violation,
            "candidate_id": (review.get("candidate") or {}).get("candidate_id"),
            "prompt_mode": "setup_review",
            "raw_response_preview": review.get("raw_response_preview") or raw[:1000],
        }
        for violation in review.get("enum_violations", [])
    ]
    return {
        "candidate_id": (review.get("candidate") or {}).get("candidate_id"),
        "prompt_mode": "setup_review",
        "parser_error": review.get("parser_error"),
        "response_length": review.get("response_length", len(raw)),
        "raw_response_preview": review.get("raw_response_preview") or raw[:1000],
        "probable_cause": _classify(raw, str(review.get("parser_error") or "")),
        "decision_if_identifiable": _decision_if_identifiable(raw),
        "enum_violations": enum_violations,
        "recommendation": "Renforcer la sortie JSON stricte et reduire les champs ambigus.",
    }


def _classify(raw: str, error: str) -> str:
    text = raw.strip()
    lowered = f"{text} {error}".lower()
    if "```" in text:
        return "markdown"
    if text and not text.startswith("{") and "{" in text:
        return "texte hors JSON"
    if "unclosed" in lowered or (text.count("{") > text.count("}")):
        return "JSON tronque"
    if "field required" in lowered or "missing" in lowered:
        return "champ manquant"
    if (
        "enum" in lowered
        or "literal" in lowered
        or "string_pattern_mismatch" in lowered
        or "pattern" in lowered
    ):
        return "valeur hors contrat"
    if "json" in lowered and ("comma" in lowered or "delimiter" in lowered):
        return "virgule/commentaire invalide"
    return "autre"


def _decision_if_identifiable(raw: str) -> str | None:
    for decision in ["NO_TRADE", "LONG", "SHORT", "HOLD", "CLOSE"]:
        if f'"decision":"{decision}"' in raw or f'"decision": "{decision}"' in raw:
            return decision
    return None


def _recommendations(causes: Counter[str]) -> list[str]:
    recommendations = ["Garder CRITICAL OUTPUT RULE au tout debut du prompt."]
    if causes.get("champ manquant"):
        recommendations.append("Ajouter un exemple JSON minimal complet dans le prompt.")
    if causes.get("valeur hors contrat"):
        recommendations.append(
            "Renforcer les valeurs autorisees champ par champ, notamment setup_quality."
        )
    if causes.get("texte hors JSON") or causes.get("markdown"):
        recommendations.append("Rappeler: pas de markdown, pas de texte avant/apres JSON.")
    if causes.get("JSON tronque"):
        recommendations.append("Reduire la longueur du prompt ou des champs reasoning_summary.")
    return recommendations


def _top_invalid_enum_values(violations: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(
        f"{violation.get('field_name')}={violation.get('invalid_value')}"
        for violation in violations
    )
    return dict(counter.most_common(10))


def _enum_violations_by_field(violations: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(str(violation.get("field_name")) for violation in violations)
    return dict(counter)


def _markdown(analysis: dict[str, Any]) -> str:
    lines = [
        "# Parser fallbacks V1.8C.7",
        "",
        f"- Source : {analysis['source_report']}",
        f"- Reviews : {analysis['total_reviews']}",
        f"- Parser fallbacks : {analysis['parser_fallback_count']}",
        f"- Causes : {analysis['causes']}",
        f"- Enum violations : {analysis['enum_violations_count']}",
        f"- Top invalid enum values : {analysis['top_invalid_enum_values']}",
        f"- Enum violations by field : {analysis['enum_violations_by_field']}",
        "",
        "## Recommandations",
        "",
    ]
    lines.extend(f"- {item}" for item in analysis["recommendations"])
    lines.extend(["", "## Exemples", ""])
    for item in analysis["fallbacks"][:10]:
        lines.append(
            f"- `{item['candidate_id']}` cause={item['probable_cause']} "
            f"decision={item['decision_if_identifiable']} error={item['parser_error']}"
        )
    lines.extend(["", "## Enum violations", ""])
    for item in analysis["enum_violations"][:20]:
        lines.append(
            f"- `{item.get('candidate_id')}` field={item.get('field_name')} "
            f"invalid={item.get('invalid_value')} allowed={item.get('allowed_values')}"
        )
    return "\n".join(lines)
