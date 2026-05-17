from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from galapagos.data.binance_futures_collector import BinanceFuturesCollector


def generate_derivatives_quality_report(
    snapshot: dict[str, Any],
    output_dir: str | Path,
    *,
    report_date: date | None = None,
) -> dict[str, Path]:
    report_date = report_date or datetime.now(UTC).date()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary = summarize_derivatives_quality(snapshot)
    md_path = output / f"derivatives_quality_{report_date.isoformat()}.md"
    json_path = output / f"derivatives_quality_{report_date.isoformat()}.json"
    md_path.write_text(_markdown(summary), encoding="utf-8")
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}


def collect_and_report_derivatives(symbol: str, output_dir: str | Path) -> dict[str, Path]:
    snapshot = BinanceFuturesCollector().fetch_derivatives_snapshot(symbol)
    return generate_derivatives_quality_report(snapshot, output_dir)


def summarize_derivatives_quality(snapshot: dict[str, Any]) -> dict[str, Any]:
    features = {
        key: value
        for key, value in snapshot.items()
        if isinstance(value, dict) and "status" in value
    }
    errors = [
        {"feature": key, "error_message": value.get("error_message")}
        for key, value in features.items()
        if value.get("status") == "error"
    ]
    recommendations = []
    if features.get("funding", {}).get("status") != "available":
        recommendations.append("Verifier acces Binance Futures funding via CCXT/API.")
    if features.get("open_interest", {}).get("status") != "available":
        recommendations.append("Verifier acces Binance Futures open interest via CCXT/API.")
    unsupported = [key for key, value in features.items() if value.get("status") == "not_supported"]
    if unsupported:
        recommendations.append(
            "Integrer endpoints exchange specifiques pour: " + ", ".join(sorted(unsupported))
        )
    return {
        "symbol": snapshot.get("symbol"),
        "provider": snapshot.get("provider"),
        "collected_at_utc": snapshot.get("collected_at_utc"),
        "features": {key: value.get("status") for key, value in features.items()},
        "errors": errors,
        "sources": {key: value.get("source") for key, value in features.items()},
        "recommendations": recommendations,
        "raw_snapshot": snapshot,
    }


def _markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Qualite donnees derivees - {summary['symbol']}",
        "",
        f"- Provider: {summary.get('provider')}",
        f"- Collected at UTC: {summary.get('collected_at_utc')}",
        "",
        "## Disponibilite",
    ]
    for feature, status in summary["features"].items():
        lines.append(f"- {feature}: {status}")
    lines.extend(["", "## Erreurs"])
    lines.extend(
        [f"- {item['feature']}: {item['error_message']}" for item in summary["errors"]]
        or ["- Aucune"]
    )
    lines.extend(["", "## Recommandations"])
    lines.extend([f"- {item}" for item in summary["recommendations"]] or ["- Aucune"])
    return "\n".join(lines)

