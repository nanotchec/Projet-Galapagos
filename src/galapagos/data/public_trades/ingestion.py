from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_trades.config import (
    DISCOVERY_JSON_PATH_V7_0,
    DOC_PATH_V7_0,
    LIMITATIONS_V7_0,
    MANIFEST_PATH_V7_0,
    MARKET_TYPE,
    REPORT_JSON_PATH_V7_0,
    REPORT_MD_PATH_V7_0,
    SCHEMA_VERSION_V7_0,
    SOURCE_DISPLAY_NAME,
    SOURCE_NAME,
    SYMBOL,
    TRADE_SOURCE_TYPE,
    VENUE,
    VERSION_V7_0,
    output_path,
    raw_zip_path,
)
from galapagos.data.public_trades.discovery import count_agg_trade_zip_rows
from galapagos.data.public_trades.provenance import new_ingestion_run_id, sha256_file, utc_now_iso
from galapagos.data.public_trades.quality import assess_agg_trades_frame
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_0, BINANCE_AGG_TRADE_RAW_COLUMNS


def run_public_trades_ingestion_v7_0(
    root: Path = Path("."),
    *,
    no_network: bool = True,
    force: bool = False,
    update_project_state: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    discovery = _read_json(root / DISCOVERY_JSON_PATH_V7_0)
    if discovery.get("status") != "PASS":
        raise RuntimeError(f"V7.0 discovery must pass before ingestion: {discovery.get('errors')}")
    window = discovery["recommended_window"]
    dates = list(discovery["available_dates"])
    if not dates:
        raise RuntimeError("V7.0 discovery did not provide any available raw trade dates.")
    if no_network:
        missing = [current_date for current_date in dates if not raw_zip_path(root, current_date).exists()]
        if missing:
            raise RuntimeError(f"V7.0 --no-network requires existing raw zips: {missing}")

    created_at = utc_now_iso()
    ingestion_run_id = new_ingestion_run_id()
    raw_files: dict[str, dict[str, Any]] = {}
    frames: list[pd.DataFrame] = []
    for current_date in dates:
        path = raw_zip_path(root, current_date)
        raw_sha = sha256_file(path)
        raw_frame = parse_binance_agg_trades_zip(path)
        normalized = normalize_agg_trades(
            raw_frame,
            raw_sha=raw_sha,
            ingestion_run_id=ingestion_run_id,
        )
        raw_files[current_date] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": raw_sha,
            "bytes": path.stat().st_size,
            "rows": count_agg_trade_zip_rows(path),
        }
        frames.append(normalized)

    frame = pd.concat(frames, ignore_index=True)
    frame = frame.sort_values(["aggregate_trade_id", "event_ts"], kind="mergesort").reset_index(drop=True)
    output = output_path(root, window["window_start"], window["window_end"])
    if output.exists() and not force:
        output.unlink()
    _write_parquet(frame[AGG_TRADE_COLUMNS_V7_0], output)
    output_payload = {
        "path": output.relative_to(root).as_posix(),
        "sha256": sha256_file(output),
        "bytes": output.stat().st_size,
        "rows": int(len(frame)),
        "format": "parquet",
    }
    quality = assess_agg_trades_frame(frame[AGG_TRADE_COLUMNS_V7_0], expected_rows=len(frame))
    quality["missing_dates"] = list(discovery["missing_dates"])
    status = "PASS" if not quality["errors"] and not discovery["missing_dates"] else "FAIL"
    manifest = {
        "version": VERSION_V7_0,
        "status": status,
        "created_at_utc": created_at,
        "ingestion_run_id": ingestion_run_id,
        "source": {
            "name": SOURCE_DISPLAY_NAME,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "trade_source_type": TRADE_SOURCE_TYPE,
        },
        "discovery": {
            "first_available_date": discovery["first_available_date"],
            "last_available_date": discovery["last_available_date"],
            "window_start": window["window_start"],
            "window_end": window["window_end"],
            "total_days": window["total_days"],
            "matches_v5_0_window": window["matches_v5_0_window"],
            "v5_0_window_start": discovery["v5_0_window_start"],
            "v5_0_window_end": discovery["v5_0_window_end"],
            "missing_dates": list(discovery["missing_dates"]),
            "documented_gaps_allowed": discovery["documented_gaps_allowed"],
            "window_selection_reason": window["reason"],
        },
        "raw_files": raw_files,
        "outputs": output_payload,
        "schema_version": SCHEMA_VERSION_V7_0,
        "trade_columns": AGG_TRADE_COLUMNS_V7_0,
        "quality": quality,
        "safety": safety_flags_v7_0(),
        "limitations": LIMITATIONS_V7_0,
    }
    _write_json(root / MANIFEST_PATH_V7_0, manifest)
    _write_json(root / REPORT_JSON_PATH_V7_0, project_report_v7_0(manifest))
    markdown = render_public_trades_report_v7_0(manifest)
    _write_text(root / REPORT_MD_PATH_V7_0, markdown)
    _write_text(root / DOC_PATH_V7_0, markdown)
    if update_project_state:
        update_project_state_v7_0(root, manifest)
    return manifest


def parse_binance_agg_trades_zip(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError("Expected exactly one CSV file inside Binance aggTrades daily archive.")
        with archive.open(csv_names[0]) as handle:
            return parse_binance_agg_trades_csv(handle.read())


def parse_binance_agg_trades_csv(content: bytes | str) -> pd.DataFrame:
    text = content.decode("utf-8") if isinstance(content, bytes) else content
    first_line = text.splitlines()[0] if text.splitlines() else ""
    has_header = any(token in first_line.casefold() for token in ["agg", "price", "quantity", "trade"])
    frame = pd.read_csv(
        io.StringIO(text),
        header=0 if has_header else None,
        names=None if has_header else BINANCE_AGG_TRADE_RAW_COLUMNS,
    )
    frame.columns = [_normalize_column_name(column) for column in frame.columns]
    aliases = {
        "agg_trade_id": "aggregate_trade_id",
        "a": "aggregate_trade_id",
        "p": "price",
        "q": "quantity",
        "f": "first_trade_id",
        "l": "last_trade_id",
        "t": "trade_time",
        "transact_time": "trade_time",
        "timestamp": "trade_time",
        "time": "trade_time",
        "m": "is_buyer_maker",
        "is_buyer_maker": "is_buyer_maker",
        "m_ignore": "is_best_match",
        "is_best_match": "is_best_match",
    }
    frame = frame.rename(columns={column: aliases.get(column, column) for column in frame.columns})
    missing = [column for column in BINANCE_AGG_TRADE_RAW_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing Binance aggTrades columns: {missing}")
    return frame[BINANCE_AGG_TRADE_RAW_COLUMNS].copy()


def normalize_agg_trades(raw_frame: pd.DataFrame, *, raw_sha: str, ingestion_run_id: str) -> pd.DataFrame:
    frame = raw_frame.copy()
    integer_columns = ["aggregate_trade_id", "first_trade_id", "last_trade_id", "trade_time"]
    for column in integer_columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise").astype("int64")
    frame["price"] = pd.to_numeric(frame["price"], errors="raise").astype("float64")
    frame["quantity"] = pd.to_numeric(frame["quantity"], errors="raise").astype("float64")
    frame["is_buyer_maker"] = frame["is_buyer_maker"].map(_parse_bool).astype("bool")
    frame["is_best_match"] = frame["is_best_match"].map(_parse_bool).astype("bool")
    timestamp_unit = _detect_timestamp_unit(frame["trade_time"])
    trade_ts = pd.to_datetime(frame["trade_time"], unit=timestamp_unit, utc=True)
    normalized = pd.DataFrame(
        {
            "source": SOURCE_NAME,
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "trade_source_type": TRADE_SOURCE_TYPE,
            "aggregate_trade_id": frame["aggregate_trade_id"].astype("int64"),
            "price": frame["price"].astype("float64"),
            "quantity": frame["quantity"].astype("float64"),
            "first_trade_id": frame["first_trade_id"].astype("int64"),
            "last_trade_id": frame["last_trade_id"].astype("int64"),
            "event_ts": trade_ts,
            "trade_ts": trade_ts,
            "available_ts": trade_ts,
            "decision_ts": trade_ts,
            "is_buyer_maker": frame["is_buyer_maker"].astype("bool"),
            "is_best_match": frame["is_best_match"].astype("bool"),
            "raw_file_sha256": raw_sha,
            "ingestion_run_id": ingestion_run_id,
            "schema_version": SCHEMA_VERSION_V7_0,
        }
    )
    return normalized[AGG_TRADE_COLUMNS_V7_0]


def project_report_v7_0(manifest: dict[str, Any]) -> dict[str, Any]:
    return dict(manifest)


def render_public_trades_report_v7_0(manifest: dict[str, Any]) -> str:
    discovery = manifest["discovery"]
    output = manifest["outputs"]
    raw_rows = "\n".join(
        f"- `{date_key}` : `{payload['rows']}` lignes, `{payload['bytes']}` octets, checksum `{payload['sha256']}`"
        for date_key, payload in manifest["raw_files"].items()
    )
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Public Trades Historical Ingestion Preview V7.0

## Objectif

V7.0 ingere uniquement des trades publics historiques Binance `{manifest['source']['trade_source_type']}` pour `BTCUSDT` spot.

## Fenetre

- Fenetre : `{discovery['window_start']}` -> `{discovery['window_end']}`.
- Total jours : `{discovery['total_days']}`.
- Meme fenetre que V5.0 : `{discovery['matches_v5_0_window']}`.
- Raison : {discovery['window_selection_reason']}.

## Raw inventory

{raw_rows}

## Output

- Path : `{output['path']}`.
- Rows : `{output['rows']}`.
- SHA256 : `{output['sha256']}`.

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

V7.0 ne valide aucune strategie.
V7.0 ne produit aucune feature.
V7.0 ne produit aucun label.
V7.0 ne produit aucun dataset ML.
V7.0 ne produit aucun modele ML.
V7.0 ne produit aucun backtest.
V7.0 ne produit aucun signal de trading.
V7.0 ne produit aucun ordre.
V7.0 n'autorise aucun paper live.
V7.0 n'autorise aucun trading reel.
"""


def safety_flags_v7_0() -> dict[str, bool]:
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


def update_project_state_v7_0(root: Path, manifest: dict[str, Any]) -> None:
    project_state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(project_state_path) if project_state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V6.4",
            "candidate_version": "V7.0",
            "candidate_status": "pending_external_audit",
            "direction": "public trades historical ingestion preview",
            "public_trades_v7_0_candidate": True,
            "public_trades_v7_0_created": True,
            "features_v7_0_created": False,
            "labels_v7_0_created": False,
            "dataset_v7_0_created": False,
            "ml_v7_0_created": False,
            "model_v7_0_created": False,
            "backtest_v7_0_created": False,
            "strategy_v7_0_created": False,
            "orders_v7_0_created": False,
            "trade_source_type_v7_0": manifest["source"]["trade_source_type"],
            "public_trades_window_start_v7_0": manifest["discovery"]["window_start"],
            "public_trades_window_end_v7_0": manifest["discovery"]["window_end"],
            "public_trades_total_days_v7_0": manifest["discovery"]["total_days"],
            "public_trades_rows_v7_0": manifest["outputs"]["rows"],
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
        "last_validated_version": "V6.4",
        "candidate_version": "V7.0",
        "candidate_status": "pending_external_audit",
        "direction": "public trades historical ingestion preview",
        "trade_source_type": manifest["source"]["trade_source_type"],
        "window_start": manifest["discovery"]["window_start"],
        "window_end": manifest["discovery"]["window_end"],
        "total_days": manifest["discovery"]["total_days"],
        "raw_inventory_count": len(manifest["raw_files"]),
        "output_rows": manifest["outputs"]["rows"],
        "matches_v5_0_window": manifest["discovery"]["matches_v5_0_window"],
        "features_v7_0_created": False,
        "labels_v7_0_created": False,
        "dataset_ml_v7_0_created": False,
        "ml_v7_0_created": False,
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
                "# Latest Metrics V7.0",
                "",
                "- Derniere version validee : V6.4.",
                "- Candidate : V7.0.",
                f"- Source trades : `{manifest['source']['trade_source_type']}`.",
                f"- Fenetre : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`.",
                f"- Total jours : `{manifest['discovery']['total_days']}`.",
                f"- Raw files : `{len(manifest['raw_files'])}`.",
                f"- Lignes trades : `{manifest['outputs']['rows']}`.",
                "- Aucun feature, label, dataset ML, modele ML, backtest, strategie, ordre ou trading.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "reports/current/latest_summary.md",
        "\n".join(
            [
                "# Latest Summary V7.0",
                "",
                "V6.4 est la derniere version validee par audit externe.",
                "",
                "V7.0 est la candidate courante. Elle produit uniquement une ingestion preview data-only de trades publics historiques Binance.",
                "",
                f"Source : `{manifest['source']['trade_source_type']}`.",
                f"Fenetre : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`, `{manifest['discovery']['total_days']}` jour(s).",
                f"Lignes trades : `{manifest['outputs']['rows']}`.",
                "",
                "Aucune feature V7.0, aucun label V7.0, aucun dataset ML V7.0, aucun modele ML V7.0, aucun backtest, aucune strategie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading reel.",
                "",
                "V7.0 reste `pending_external_audit`.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "reports/PROJECT_STATE.md",
        "\n".join(
            [
                "# Etat du Projet : V6.4 validee + candidat V7.0",
                "",
                "- **Derniere version validee** : V6.4.",
                "- **Version candidate** : V7.0.",
                "- **Statut candidate** : `pending_external_audit`.",
                "- **Direction** : public trades historical ingestion preview.",
                "",
                "## V7.0",
                "",
                f"- Source trades : `{manifest['source']['trade_source_type']}`.",
                f"- Fenetre : `{manifest['discovery']['window_start']}` -> `{manifest['discovery']['window_end']}`.",
                f"- Total jours : `{manifest['discovery']['total_days']}`.",
                f"- Raw files : `{len(manifest['raw_files'])}`.",
                f"- Lignes trades : `{manifest['outputs']['rows']}`.",
                "- Aucune feature V7.0.",
                "- Aucun label V7.0.",
                "- Aucun dataset ML V7.0.",
                "- Aucun modele ML V7.0.",
                "- Aucun backtest, aucune strategie, aucun signal, aucun ordre, aucun trading reel.",
                "",
                "V7.0 reste non validee avant audit externe.",
            ]
        )
        + "\n",
    )


def _normalize_column_name(column: object) -> str:
    return str(column).strip().casefold().replace(" ", "_")


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().casefold()
    if text in {"true", "1"}:
        return True
    if text in {"false", "0"}:
        return False
    raise ValueError(f"Unsupported Binance boolean value: {value!r}")


def _detect_timestamp_unit(values: pd.Series) -> str:
    maximum = int(values.max())
    if maximum >= 10**15:
        return "us"
    if maximum >= 10**12:
        return "ms"
    if maximum >= 10**9:
        return "s"
    raise ValueError("Unsupported Binance aggTrades timestamp magnitude.")


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
