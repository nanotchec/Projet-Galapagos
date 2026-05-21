from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.config import MISSION, VERSION, PublicMarketIngestionConfig
from galapagos.data.public_market.provenance import new_ingestion_run_id, sha256_file, utc_now_iso
from galapagos.data.public_market.quality import assess_ohlcv_quality
from galapagos.data.public_market.schemas import OHLCV_COLUMNS
from galapagos.data.public_market.sources.binance_archive import (
    build_public_archive_url,
    download_public_archive,
    parse_binance_kline_zip,
)
from galapagos.data.public_market.storage import ensure_parent, write_parquet


def run_public_market_ingestion(config: PublicMarketIngestionConfig) -> dict[str, Any]:
    config.validate()
    created_at = utc_now_iso()
    ingestion_run_id = new_ingestion_run_id()
    url = build_public_archive_url(
        market_type=config.market_type,
        symbol=config.symbol,
        timeframe=config.timeframe,
        date=config.date,
    )
    network_used = False
    raw_available = config.raw_path.exists() and not config.force
    if not raw_available and config.no_network:
        raise FileNotFoundError("--no-network requires the raw public archive to already exist.")
    if not raw_available and not config.no_network:
        download_public_archive(url, config.raw_path)
        network_used = True

    raw_sha = sha256_file(config.raw_path)
    raw_frame = parse_binance_kline_zip(config.raw_path)
    silver_frame = normalize_binance_klines(
        raw_frame,
        config=config,
        raw_sha=raw_sha,
        ingestion_run_id=ingestion_run_id,
        ingested_at_ts=created_at,
    )
    write_parquet(silver_frame[OHLCV_COLUMNS], config.silver_path)
    silver_sha = sha256_file(config.silver_path)

    quality_result = assess_ohlcv_quality(silver_frame, expected_rows=config.expected_rows, timeframe=config.timeframe)
    limitations = [
        "V2.3 couvre une seule source publique read-only, un seul symbole, un seul timeframe et une seule journee.",
        "V2.3 ne valide aucune strategie, aucun modele ML, aucun signal, aucun backtest et aucun trading.",
    ]
    status = "PASS" if quality_result.passed else "FAIL"
    if config.fail_on_quality_warning and quality_result.payload["warnings"]:
        status = "FAIL"
    manifest = build_manifest(
        config=config,
        created_at=created_at,
        ingestion_run_id=ingestion_run_id,
        network_used=network_used,
        raw_sha=raw_sha,
        silver_sha=silver_sha,
        quality=quality_result.payload,
        limitations=limitations,
        status=status,
    )
    quality_report = build_quality_report(manifest=manifest, url=url)
    write_json(config.manifest_path, manifest)
    write_json(config.quality_json_path, quality_report)
    write_markdown(config.quality_md_path, quality_report)
    return manifest


def normalize_binance_klines(
    frame: pd.DataFrame,
    *,
    config: PublicMarketIngestionConfig,
    raw_sha: str,
    ingestion_run_id: str,
    ingested_at_ts: str,
) -> pd.DataFrame:
    normalized = pd.DataFrame(index=frame.index)
    normalized["source"] = "binance_archive"
    normalized["venue"] = "binance"
    normalized["market_type"] = config.market_type
    normalized["symbol"] = config.symbol
    normalized["timeframe"] = config.timeframe
    normalized["event_ts"] = pd.to_datetime(frame["event_ts"], utc=True)
    normalized["close_ts"] = pd.to_datetime(frame["close_ts"], utc=True)
    normalized["available_ts"] = normalized["close_ts"]
    normalized["decision_ts"] = normalized["available_ts"]
    normalized["ingested_at_ts"] = pd.to_datetime(ingested_at_ts, utc=True)
    for column in ["open", "high", "low", "close", "volume"]:
        normalized[column] = frame[column].astype("float64")
    normalized["quote_volume"] = frame["quote_volume"].astype("float64")
    normalized["trade_count"] = frame["trade_count"].astype("int64")
    normalized["taker_buy_base_volume"] = frame["taker_buy_base_volume"].astype("float64")
    normalized["taker_buy_quote_volume"] = frame["taker_buy_quote_volume"].astype("float64")
    normalized["source_open_time_raw"] = frame["open_time"].astype("int64")
    normalized["source_close_time_raw"] = frame["close_time"].astype("int64")
    normalized["source_timestamp_unit"] = frame["source_timestamp_unit"].astype("string")
    normalized["raw_file_sha256"] = raw_sha
    normalized["ingestion_run_id"] = ingestion_run_id
    return normalized.sort_values("event_ts").reset_index(drop=True)


def build_manifest(
    *,
    config: PublicMarketIngestionConfig,
    created_at: str,
    ingestion_run_id: str,
    network_used: bool,
    raw_sha: str,
    silver_sha: str,
    quality: dict[str, Any],
    limitations: list[str],
    status: str,
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "correction_version": "V2.3.1",
        "mission": MISSION,
        "status": status,
        "created_at_utc": created_at,
        "ingestion_run_id": ingestion_run_id,
        "network_used": network_used,
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "ml_enabled": False,
        "labels_enabled": False,
        "backtest_enabled": False,
        "source": {
            "name": "binance_public_archive",
            "venue": "binance",
            "market_type": config.market_type,
            "symbol": config.symbol,
            "timeframe": config.timeframe,
            "date": config.date,
        },
        "raw": {
            "path": str(config.raw_path),
            "sha256": raw_sha,
            "bytes": config.raw_path.stat().st_size,
        },
        "silver": {
            "path": str(config.silver_path),
            "sha256": silver_sha,
            "bytes": config.silver_path.stat().st_size,
            "format": "parquet",
        },
        "quality": quality,
        "limitations": limitations,
    }


def build_quality_report(*, manifest: dict[str, Any], url: str) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "correction_version": manifest.get("correction_version"),
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "ingestion_run_id": manifest["ingestion_run_id"],
        "source_url": url,
        "source": manifest["source"],
        "quality": manifest["quality"],
        "raw_checksum": manifest["raw"]["sha256"],
        "silver_checksum": manifest["silver"]["sha256"],
        "raw_path": manifest["raw"]["path"],
        "silver_path": manifest["silver"]["path"],
        "safety": {
            "public_read_only": True,
            "authentication_used": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "orders_enabled": False,
            "paper_live_enabled": False,
            "trading_enabled": False,
            "ml_enabled": False,
            "labels_enabled": False,
            "backtest_enabled": False,
        },
        "limitations": manifest["limitations"],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    source = payload["source"]
    quality = payload["quality"]
    safety = payload["safety"]
    gaps = "\n".join(
        f"- {gap['previous_event_ts']} -> {gap['next_event_ts']} ({gap['delta_seconds']} s)"
        for gap in quality.get("gaps", [])
    ) or "- Aucun trou detecte."
    limitations = "\n".join(f"- {item}" for item in payload["limitations"])
    text = f"""# Public Market Ingestion V2.3

## Statut

- Statut final : `{payload['status']}`
- Source : `{source['name']}`
- Symbole : `{source['symbol']}`
- Timeframe : `{source['timeframe']}`
- Date : `{source['date']}`
- Run : `{payload['ingestion_run_id']}`

## Qualite physique

- Lignes : `{quality['rows']}`
- Lignes attendues : `{quality['expected_rows']}`
- Min event_ts : `{quality['min_event_ts']}`
- Max event_ts : `{quality['max_event_ts']}`
- Min close_ts : `{quality['min_close_ts']}`
- Max close_ts : `{quality['max_close_ts']}`
- Doublons : `{quality['duplicate_rows']}`
- Trous temporels : `{quality['gap_count']}`
- Violations OHLC : `{quality['ohlc_violations']}`
- Volumes negatifs : `{quality['negative_volume_rows']}`
- Lignes avec null critique : `{quality['null_critical_rows']}`
- Checksum raw : `{payload['raw_checksum']}`
- Checksum silver : `{payload['silver_checksum']}`

## Details des trous

{gaps}

## Securite

- Public read-only : `{safety['public_read_only']}`
- Authentification : `{safety['authentication_used']}`
- Cle API : `{safety['api_key_used']}`
- Endpoint prive : `{safety['private_endpoint_used']}`
- Ordres : `{safety['orders_enabled']}`
- Paper live : `{safety['paper_live_enabled']}`
- Trading : `{safety['trading_enabled']}`
- ML : `{safety['ml_enabled']}`
- Labels : `{safety['labels_enabled']}`
- Backtest : `{safety['backtest_enabled']}`

## Limitations

{limitations}

V2.3 ne valide aucune strategie. V2.3 ne valide aucun modele ML. V2.3 ne produit aucun signal de trading. V2.3 ne produit aucun ordre. V2.3 n'autorise aucun paper live. V2.3 est uniquement une preview d'ingestion de donnees publiques reelles.
"""
    path.write_text(text, encoding="utf-8")
