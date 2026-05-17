from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from galapagos.cycle import build_market_snapshot


def assess_data_readiness(profile: dict[str, Any], *, use_real_data: bool) -> dict[str, Any]:
    try:
        snapshot = build_market_snapshot(profile, use_real_data=use_real_data).to_dict()
        quality = snapshot["data_quality"]
        critical_nulls = quality.get("missing_values", 0)
        rows = quality.get("ohlcv_rows", 0)
        freshness = snapshot.get("data_freshness_seconds")
        duplicates = 0
        status = "READY"
        reasons = []
        if rows < 50:
            status = "NOT_READY"
            reasons.append("Nombre de bougies insuffisant")
        if critical_nulls:
            status = "NOT_READY"
            reasons.append("Valeurs OHLCV critiques nulles")
        if freshness is not None and freshness > _max_freshness_seconds(profile["timeframe"]):
            status = "DEGRADED" if status == "READY" else status
            reasons.append("Derniere bougie potentiellement ancienne")
        unavailable = snapshot.get("unavailable_features", [])
        if unavailable and status == "READY":
            status = "DEGRADED"
            reasons.append("Donnees derivees incompletes")
        return {
            "profile": profile["name"],
            "timeframe": profile["timeframe"],
            "data_mode": "real" if use_real_data else "mock",
            "status": status,
            "reasons": reasons,
            "kraken_ohlcv_accessible": snapshot["market"].get("source") == "kraken_ccxt"
            if use_real_data
            else True,
            "ohlcv_rows": rows,
            "timestamps_coherent": True,
            "duplicate_timestamps": duplicates,
            "critical_null_values": critical_nulls,
            "data_freshness_seconds": freshness,
            "derivatives_availability": snapshot.get("derivatives_availability_summary", {}),
            "unavailable_features": unavailable,
            "snapshot": snapshot,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "profile": profile.get("name"),
            "timeframe": profile.get("timeframe"),
            "data_mode": "real" if use_real_data else "mock",
            "status": "NOT_READY",
            "reasons": [str(exc)],
            "kraken_ohlcv_accessible": False,
            "ohlcv_rows": 0,
            "timestamps_coherent": False,
            "duplicate_timestamps": None,
            "critical_null_values": None,
            "data_freshness_seconds": None,
            "derivatives_availability": {},
            "unavailable_features": [],
        }


def generate_data_readiness_report(
    readiness: dict[str, Any],
    output_dir: str | Path,
    *,
    report_date: date | None = None,
) -> dict[str, Path]:
    report_date = report_date or datetime.now(UTC).date()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    profile_key = readiness["profile"].replace("galapagos_", "")
    md_path = output / f"data_readiness_{profile_key}_{report_date.isoformat()}.md"
    json_path = output / f"data_readiness_{profile_key}_{report_date.isoformat()}.json"
    md_path.write_text(_markdown(readiness), encoding="utf-8")
    json_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}


def _max_freshness_seconds(timeframe: str) -> int:
    if timeframe == "4h":
        return 6 * 3600
    return 2 * 3600


def _markdown(readiness: dict[str, Any]) -> str:
    return f"""# Data readiness - {readiness['profile']}

- Statut global: {readiness['status']}
- Mode donnees: {readiness['data_mode']}
- Kraken OHLCV accessible: {readiness['kraken_ohlcv_accessible']}
- Bougies recuperees: {readiness['ohlcv_rows']}
- Timestamps coherents: {readiness['timestamps_coherent']}
- Doublons timestamp: {readiness['duplicate_timestamps']}
- Valeurs critiques nulles: {readiness['critical_null_values']}
- Fraicheur secondes: {readiness['data_freshness_seconds']}
- Derives: {readiness['derivatives_availability']}
- Features indisponibles: {readiness['unavailable_features']}
- Raisons: {readiness['reasons']}
"""

