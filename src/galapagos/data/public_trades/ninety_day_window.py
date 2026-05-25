from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_trades.config import (
    DEFAULT_90D_WINDOW_END_V7_7,
    DEFAULT_90D_WINDOW_START_V7_7,
    DISCOVERY_JSON_PATH_V7_7,
    DISCOVERY_MD_PATH_V7_7,
    DOC_PATH_V7_7,
    LIMITATIONS_V7_7,
    MANIFEST_PATH_V7_7,
    MARKET_TYPE,
    REPORT_JSON_PATH_V7_7,
    REPORT_MD_PATH_V7_7,
    SCHEMA_VERSION_V7_7,
    SOURCE_DISPLAY_NAME,
    SYMBOL,
    TRADE_SOURCE_TYPE,
    V5_0_MANIFEST_PATH,
    VENUE,
    VERSION_V7_7,
    output_partition_path_v7_7,
    raw_zip_path,
)
from galapagos.data.public_trades.discovery import (
    _download_public_archive,
    _probe_public_archive,
    build_public_trades_archive_url,
    count_agg_trade_zip_rows,
)
from galapagos.data.public_trades.ninety_day_window_quality import assess_ninety_day_agg_trade_partitions_v7_7
from galapagos.data.public_trades.ingestion import normalize_agg_trades, parse_binance_agg_trades_zip
from galapagos.data.public_trades.provenance import new_ingestion_run_id, sha256_file, utc_now_iso
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_7


def discover_public_trades_90d_window_v7_7(
    root: Path = Path("."),
    *,
    start_date: str = DEFAULT_90D_WINDOW_START_V7_7,
    end_date: str = DEFAULT_90D_WINDOW_END_V7_7,
    allow_documented_gaps: bool = False,
    no_network: bool = False,
) -> dict[str, Any]:
    project_root = root.resolve()
    v5_manifest = _read_json(project_root / V5_0_MANIFEST_PATH)
    v5_window_start = v5_manifest["discovery"]["window_start"]
    v5_window_end = v5_manifest["discovery"]["window_end"]
    if start_date < v5_window_start or end_date > v5_window_end:
        raise ValueError("V7.7 window must remain inside the V5.0 validated OHLCV window.")
    selected_dates = _date_range(start_date, end_date)
    available_dates: list[str] = []
    missing_dates: list[str] = []
    remote_files: dict[str, dict[str, Any]] = {}

    for current_date in selected_dates:
        local_raw = raw_zip_path(project_root, current_date)
        if local_raw.exists():
            available_dates.append(current_date)
            continue
        if no_network:
            missing_dates.append(current_date)
            continue
        url = build_public_trades_archive_url(date_value=current_date)
        probe = _probe_public_archive(url)
        remote_files[current_date] = probe
        if probe["available"]:
            _download_public_archive(url, local_raw)
            available_dates.append(current_date)
        else:
            missing_dates.append(current_date)

    raw_inventory = {
        current_date: _raw_inventory_entry(project_root, current_date)
        for current_date in available_dates
        if raw_zip_path(project_root, current_date).exists()
    }
    total_days = len(selected_dates)
    reason = "bounded 90-day V7.7 aggTrades expansion after the 30-day V7.1 ingestion window and V7.6 decision gate"
    errors = []
    if missing_dates and not allow_documented_gaps:
        errors.append(f"missing aggTrades dates in selected V7.7 window: {missing_dates}")
    discovery = {
        "version": VERSION_V7_7,
        "status": "PASS" if not errors else "FAIL",
        "created_at_utc": utc_now_iso(),
        "source": {
            "name": SOURCE_DISPLAY_NAME,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "trade_source_type": TRADE_SOURCE_TYPE,
            "host": "data.binance.vision",
        },
        "first_available_date": available_dates[0] if available_dates else None,
        "last_available_date": available_dates[-1] if available_dates else None,
        "available_dates": available_dates,
        "missing_dates": missing_dates,
        "total_available_days": len(available_dates),
        "source_type": TRADE_SOURCE_TYPE,
        "v5_0_window_start": v5_window_start,
        "v5_0_window_end": v5_window_end,
        "overlap_start": start_date if available_dates else None,
        "overlap_end": end_date if available_dates else None,
        "overlap_days": len(available_dates),
        "recommended_window": {
            "window_start": start_date,
            "window_end": end_date,
            "total_days": total_days,
            "matches_v5_0_window": False,
            "reason": reason,
        },
        "remote_files": remote_files,
        "raw_files": raw_inventory,
        "documented_gaps_allowed": allow_documented_gaps,
        "errors": errors,
        "warnings": [reason],
    }
    _write_json(project_root / DISCOVERY_JSON_PATH_V7_7, discovery)
    _write_text(project_root / DISCOVERY_MD_PATH_V7_7, render_discovery_markdown_v7_7(discovery))
    return discovery


def run_public_trades_90d_window_v7_7(
    root: Path = Path("."),
    *,
    no_network: bool = True,
    force: bool = False,
    update_project_state: bool = True,
) -> dict[str, Any]:
    project_root = root.resolve()
    discovery = _read_json(project_root / DISCOVERY_JSON_PATH_V7_7)
    if discovery.get("status") != "PASS":
        raise RuntimeError(f"V7.7 discovery must pass before ingestion: {discovery.get('errors')}")
    window = discovery["recommended_window"]
    dates = list(discovery["available_dates"])
    if no_network:
        missing = [current_date for current_date in dates if not raw_zip_path(project_root, current_date).exists()]
        if missing:
            raise RuntimeError(f"V7.7 --no-network requires existing raw zips: {missing}")

    ingestion_run_id = new_ingestion_run_id()
    raw_files: dict[str, dict[str, Any]] = {}
    partitions: dict[str, dict[str, Any]] = {}
    total_rows = 0
    total_bytes = 0
    for current_date in dates:
        raw_path = raw_zip_path(project_root, current_date)
        raw_sha = sha256_file(raw_path)
        raw_frame = parse_binance_agg_trades_zip(raw_path)
        normalized = normalize_agg_trades(
            raw_frame,
            raw_sha=raw_sha,
            ingestion_run_id=ingestion_run_id,
            schema_version=SCHEMA_VERSION_V7_7,
            columns=AGG_TRADE_COLUMNS_V7_7,
        )
        normalized = normalized.sort_values(["aggregate_trade_id", "event_ts"], kind="mergesort").reset_index(drop=True)
        output_path = output_partition_path_v7_7(project_root, window["window_start"], window["window_end"], current_date)
        if output_path.exists():
            if force:
                output_path.unlink()
            else:
                output_path.unlink()
        _write_parquet(normalized[AGG_TRADE_COLUMNS_V7_7], output_path)
        event_ts = pd.to_datetime(normalized["event_ts"], utc=True)
        raw_files[current_date] = {
            "path": raw_path.relative_to(project_root).as_posix(),
            "sha256": raw_sha,
            "bytes": raw_path.stat().st_size,
            "rows": count_agg_trade_zip_rows(raw_path),
        }
        partitions[current_date] = {
            "path": output_path.relative_to(project_root).as_posix(),
            "sha256": sha256_file(output_path),
            "bytes": output_path.stat().st_size,
            "rows": int(len(normalized)),
            "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z"),
            "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z"),
            "raw_file_sha256": raw_sha,
        }
        total_rows += int(len(normalized))
        total_bytes += output_path.stat().st_size

    quality = assess_ninety_day_agg_trade_partitions_v7_7(
        project_root,
        partitions,
        expected_days=window["total_days"],
        missing_dates=list(discovery["missing_dates"]),
    )
    status = "PASS" if not quality["errors"] and not discovery["missing_dates"] else "FAIL"
    manifest = {
        "version": VERSION_V7_7,
        "status": status,
        "created_at_utc": utc_now_iso(),
        "ingestion_run_id": ingestion_run_id,
        "source": {
            "name": SOURCE_DISPLAY_NAME,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "trade_source_type": TRADE_SOURCE_TYPE,
        },
        "discovery": {
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "total_days": window["total_days"],
            "matches_v5_0_window": False,
            "v5_0_window_start": discovery["v5_0_window_start"],
            "v5_0_window_end": discovery["v5_0_window_end"],
            "missing_dates": list(discovery["missing_dates"]),
            "documented_gaps_allowed": discovery["documented_gaps_allowed"],
            "window_selection_reason": window["reason"],
        },
        "raw_files": raw_files,
        "outputs": {
            "partitions": partitions,
            "total_rows": int(total_rows),
            "total_bytes": int(total_bytes),
            "format": "partitioned_parquet",
        },
        "schema_version": SCHEMA_VERSION_V7_7,
        "trade_columns": AGG_TRADE_COLUMNS_V7_7,
        "quality": quality,
        "safety": safety_flags_v7_7(),
        "limitations": LIMITATIONS_V7_7,
    }
    _write_json(project_root / MANIFEST_PATH_V7_7, manifest)
    _write_json(project_root / REPORT_JSON_PATH_V7_7, project_report_v7_7(manifest))
    markdown = render_public_trades_report_v7_7(manifest)
    _write_text(project_root / REPORT_MD_PATH_V7_7, markdown)
    _write_text(project_root / DOC_PATH_V7_7, markdown)
    if update_project_state:
        update_project_state_v7_7(project_root, manifest)
    return manifest


def render_discovery_markdown_v7_7(discovery: dict[str, Any]) -> str:
    window = discovery["recommended_window"]
    missing = "\n".join(f"- `{item}`" for item in discovery["missing_dates"]) or "- Aucune"
    raw = "\n".join(
        f"- `{date_key}` : `{payload['path']}`, `{payload['rows']}` lignes, `{payload['bytes']}` octets"
        for date_key, payload in discovery["raw_files"].items()
    ) or "- Aucun"
    warnings = "\n".join(f"- {item}" for item in discovery["warnings"]) or "- Aucune"
    return f"""# Discovery trades publics V7.7

V7.7 decouvre une fenetre bornee de 90 jours de trades publics Binance `{discovery['source_type']}` pour `BTCUSDT` spot.

## Fenetre

- Fenetre V5.0 : `{discovery['v5_0_window_start']}` -> `{discovery['v5_0_window_end']}`.
- Fenetre V7.7 retenue : `{window['window_start']}` -> `{window['window_end']}`.
- Total jours V7.7 : `{window['total_days']}`.
- Meme fenetre que V5.0 : `{window['matches_v5_0_window']}`.
- Raison : {window['reason']}.

## Disponibilite

- Premiere date disponible decouverte : `{discovery['first_available_date']}`.
- Derniere date disponible decouverte : `{discovery['last_available_date']}`.
- Jours disponibles : `{discovery['total_available_days']}`.
- Trous documentes autorises : `{discovery['documented_gaps_allowed']}`.

## Dates manquantes

{missing}

## Raw inventory

{raw}

## Avertissements

{warnings}

V7.7 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.
"""


def project_report_v7_7(manifest: dict[str, Any]) -> dict[str, Any]:
    return dict(manifest)


def render_public_trades_report_v7_7(manifest: dict[str, Any]) -> str:
    discovery = manifest["discovery"]
    outputs = manifest["outputs"]
    raw_rows = "\n".join(
        f"- `{date_key}` : `{payload['rows']}` lignes, `{payload['bytes']}` octets, checksum `{payload['sha256']}`"
        for date_key, payload in manifest["raw_files"].items()
    )
    partition_rows = "\n".join(
        f"- `{date_key}` : `{payload['path']}`, `{payload['rows']}` lignes, checksum `{payload['sha256']}`"
        for date_key, payload in outputs["partitions"].items()
    )
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Public Trades Historical Window Expansion V7.7

## Objectif

V7.7 etend uniquement l'ingestion data-only de trades publics Binance `{manifest['source']['trade_source_type']}` pour `BTCUSDT` spot.

## Fenetre

- Fenetre : `{discovery['window_start']}` -> `{discovery['window_end']}`.
- Total jours : `{discovery['total_days']}`.
- Meme fenetre que V5.0 : `{discovery['matches_v5_0_window']}`.
- Raison : {discovery['window_selection_reason']}.

## Raw inventory

{raw_rows}

## Outputs partitionnes

- Rows totales : `{outputs['total_rows']}`.
- Bytes totaux : `{outputs['total_bytes']}`.
- Format : `{outputs['format']}`.

{partition_rows}

## Qualite

- Doublons `aggregate_trade_id` : `{manifest['quality']['duplicate_aggregate_trade_ids']}`.
- IDs non monotones : `{manifest['quality']['non_monotonic_trade_ids']}`.
- Timestamps non monotones : `{manifest['quality']['non_monotonic_event_ts']}`.
- Prix non positifs : `{manifest['quality']['price_non_positive_rows']}`.
- Quantites non positives : `{manifest['quality']['quantity_non_positive_rows']}`.
- Colonnes interdites : `{manifest['quality']['forbidden_columns_present']}`.

## Limitations

{limitations}

## Securite

V7.7 ne valide aucune strategie.
V7.7 ne produit aucune feature.
V7.7 ne produit aucun label.
V7.7 ne produit aucun dataset ML.
V7.7 ne produit aucun modele ML.
V7.7 ne produit aucun backtest.
V7.7 ne produit aucun signal de trading.
V7.7 ne produit aucun ordre.
V7.7 n'autorise aucun paper live.
V7.7 n'autorise aucun trading reel.
"""


def safety_flags_v7_7() -> dict[str, bool]:
    return {
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "ml_enabled": False,
        "labels_enabled": False,
        "dataset_enabled": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
    }


def update_project_state_v7_7(root: Path, manifest: dict[str, Any]) -> None:
    project_state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(project_state_path) if project_state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V7.6",
            "candidate_version": "V7.7",
            "candidate_status": "pending_external_audit",
            "direction": "public aggTrades 90-day window expansion",
            "public_trades_v7_7_candidate": True,
            "public_trades_v7_7_created": True,
            "features_v7_7_created": False,
            "labels_v7_7_created": False,
            "dataset_v7_7_created": False,
            "ml_v7_7_created": False,
            "model_v7_7_created": False,
            "backtest_v7_7_created": False,
            "strategy_v7_7_created": False,
            "orders_v7_7_created": False,
            "trade_source_type_v7_7": manifest["source"]["trade_source_type"],
            "public_trades_window_start_v7_7": manifest["discovery"]["window_start"],
            "public_trades_window_end_v7_7": manifest["discovery"]["window_end"],
            "public_trades_total_days_v7_7": manifest["discovery"]["total_days"],
            "public_trades_rows_v7_7": manifest["outputs"]["total_rows"],
            "backtest_enabled": False,
            "strategy_enabled": False,
            "paper_live_enabled": False,
            "orders_enabled": False,
            "trading_enabled": False,
            "execution_enabled": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "authentication_used": False,
            "external_validation_required": True,
        }
    )
    _write_json(project_state_path, state)
    _write_current_reports(root, manifest)


def _write_current_reports(root: Path, manifest: dict[str, Any]) -> None:
    latest_metrics = {
        "last_validated_version": "V7.6",
        "candidate_version": "V7.7",
        "candidate_status": "pending_external_audit",
        "direction": "public aggTrades 90-day window expansion",
        "trade_source_type": manifest["source"]["trade_source_type"],
        "window_start": manifest["discovery"]["window_start"],
        "window_end": manifest["discovery"]["window_end"],
        "total_days": manifest["discovery"]["total_days"],
        "raw_inventory_count": len(manifest["raw_files"]),
        "output_rows": manifest["outputs"]["total_rows"],
        "output_partitions": len(manifest["outputs"]["partitions"]),
        "matches_v5_0_window": manifest["discovery"]["matches_v5_0_window"],
        "features_v7_7_created": False,
        "labels_v7_7_created": False,
        "dataset_ml_v7_7_created": False,
        "ml_v7_7_created": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "execution_enabled": False,
        "external_validation_required": True,
    }
    _write_json(root / "reports/current/latest_metrics.json", latest_metrics)
    _write_text(
        root / "reports/current/latest_metrics.md",
        "\n".join(
            [
                "# Latest Metrics V7.7",
                "",
                "- Derniere version validee : V7.6.",
                "- Candidate : V7.7.",
                f"- Source trades : `{manifest['source']['trade_source_type']}`.",
                f"- Fenetre : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`.",
                f"- Total jours : `{manifest['discovery']['total_days']}`.",
                f"- Raw files : `{len(manifest['raw_files'])}`.",
                f"- Partitions : `{len(manifest['outputs']['partitions'])}`.",
                f"- Lignes trades : `{manifest['outputs']['total_rows']}`.",
                "- Aucun feature, label, dataset ML, modele ML, backtest, strategie, ordre ou trading.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "reports/current/latest_summary.md",
        "\n".join(
            [
                "# Latest Summary V7.7",
                "",
                "V7.6 est la derniere version validee localement.",
                "",
                "V7.7 est la candidate courante. Elle etend uniquement l'ingestion data-only de trades publics Binance aggTrades sur une fenetre bornee de 90 jours.",
                "",
                f"Source : `{manifest['source']['trade_source_type']}`.",
                f"Fenetre : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`, `{manifest['discovery']['total_days']}` jours.",
                f"Lignes trades : `{manifest['outputs']['total_rows']}`.",
                "",
                "Aucune feature V7.7, aucun label V7.7, aucun dataset ML V7.7, aucun modele ML V7.7, aucun backtest, aucune strategie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading reel.",
                "",
                "V7.7 reste `pending_external_audit`.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "reports/PROJECT_STATE.md",
        "\n".join(
            [
                "# Etat du Projet : V7.6 validee + candidat V7.7",
                "",
                "- **Derniere version validee** : V7.6.",
                "- **Version candidate** : V7.7.",
                "- **Statut candidate** : `pending_external_audit`.",
                "- **Direction** : public aggTrades 90-day window expansion.",
                "",
                "## V7.7",
                "",
                f"- Source trades : `{manifest['source']['trade_source_type']}`.",
                f"- Fenetre : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`.",
                f"- Total jours : `{manifest['discovery']['total_days']}`.",
                f"- Raw files : `{len(manifest['raw_files'])}`.",
                f"- Partitions : `{len(manifest['outputs']['partitions'])}`.",
                f"- Lignes trades : `{manifest['outputs']['total_rows']}`.",
                "- Aucune feature V7.7.",
                "- Aucun label V7.7.",
                "- Aucun dataset ML V7.7.",
                "- Aucun modele ML V7.7.",
                "- Aucun backtest, aucune strategie, aucun signal, aucun ordre, aucun trading reel.",
                "",
                "V7.7 reste non validee avant audit externe.",
            ]
        )
        + "\n",
    )


def _raw_inventory_entry(root: Path, current_date: str) -> dict[str, Any]:
    path = raw_zip_path(root, current_date)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": count_agg_trade_zip_rows(path),
    }


def _date_range(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    days = (end_date - start_date).days + 1
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range(days)]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False, engine="pyarrow")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
