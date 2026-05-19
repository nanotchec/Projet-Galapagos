from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import ensure_parent, read_parquet, write_parquet
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4, resampled_silver_path
from galapagos.features.schemas import FEATURE_COLUMNS_V2_5
from galapagos.features.registry import (
    VERSION,
    CORRECTION_VERSION,
    MANIFEST_PATH,
    QUALITY_JSON_PATH,
    QUALITY_MD_PATH,
    TARGET_TIMEFRAMES,
    get_feature_gold_path,
)
from galapagos.features.causal_ohlcv import build_causal_features
from galapagos.features.quality import assess_feature_quality

EXPECTED_LIMITATIONS_V2_5 = [
    "V2.5 produit uniquement des features OHLCV causales sur BTCUSDT 2024-01-15 a partir des donnees V2.4 validees.",
    "V2.5 ne produit aucun label, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre."
]


def run_feature_store_generation(root: Path = Path("."), feature_run_id: str | None = None) -> dict[str, Any]:
    """Generates the V2.5 causal feature store preview."""
    root = root.resolve()
    
    # 1. Validate previous stages
    ingestion_validation = validate_public_market_ingestion_v2_3(root)
    if not ingestion_validation["passed"]:
        raise RuntimeError(f"V2.3.1 input validation failed: {ingestion_validation['errors']}")
        
    resampling_validation = validate_ohlcv_resampling_v2_4(root)
    if not resampling_validation["passed"]:
        raise RuntimeError(f"V2.4.8 resampling validation failed: {resampling_validation['errors']}")
        
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    if not feature_run_id:
        feature_run_id = f"v2_5_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
        
    input_ohlcv: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    qualities: dict[str, dict[str, Any]] = {}
    
    status = "PASS"
    
    for tf in TARGET_TIMEFRAMES:
        input_path = resampled_silver_path(root, tf)
        gold_path = get_feature_gold_path(root, tf)
        
        # Load silver OHLCV
        df_silver = read_parquet(input_path)
        sha_silver = sha256_file(input_path)
        
        # Build features
        df_gold = build_causal_features(df_silver, sha_silver, feature_run_id)
        write_parquet(df_gold, gold_path)
        
        # Ingestion metrics
        input_ohlcv[tf] = {
            "path": str(input_path.relative_to(root)),
            "sha256": sha_silver,
            "rows": int(len(df_silver)),
        }
        
        # Gold features metrics
        outputs[tf] = {
            "path": str(gold_path.relative_to(root)),
            "sha256": sha256_file(gold_path),
            "bytes": gold_path.stat().st_size,
            "rows": int(len(df_gold)),
            "format": "parquet",
        }
        
        # Quality assessment
        quality = assess_feature_quality(df_gold, len(df_silver), tf)
        qualities[tf] = quality
        if quality["errors"]:
            status = "FAIL"
            
    manifest = {
        "version": VERSION,
        "correction_version": CORRECTION_VERSION,
        "status": status,
        "created_at_utc": created_at,
        "feature_run_id": feature_run_id,
        "input_ohlcv": input_ohlcv,
        "outputs": outputs,
        "feature_schema_version": "V2.5",
        "feature_columns": FEATURE_COLUMNS_V2_5,
        "quality": qualities,
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
        "limitations": EXPECTED_LIMITATIONS_V2_5,
    }
    
    report = _build_report(manifest)
    
    # Save artifacts
    _write_json(root / MANIFEST_PATH, manifest)
    _write_json(root / QUALITY_JSON_PATH, report)
    _write_markdown(root / QUALITY_MD_PATH, report)
    
    return manifest


def _build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "correction_version": manifest.get("correction_version"),
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "feature_run_id": manifest["feature_run_id"],
        "input_ohlcv": manifest["input_ohlcv"],
        "outputs": manifest["outputs"],
        "feature_schema_version": manifest["feature_schema_version"],
        "feature_columns": manifest["feature_columns"],
        "quality": manifest["quality"],
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    lines = [
        "# Causal Feature Store V2.5",
        "",
        f"- Statut : `{payload['status']}`",
        f"- Run ID : `{payload['feature_run_id']}`",
        f"- Feature Schema Version : `{payload['feature_schema_version']}`",
        "",
        "## Lignes de features gold produites",
        "",
    ]
    for tf in TARGET_TIMEFRAMES:
        quality = payload["quality"][tf]
        lines.append(f"- `{tf}` : `{quality['rows']}` features (Warmup: `{quality['warmup_rows']}` lignes, Lignes actives après warmup: `{quality['rows_after_warmup']}`)")
        
    lines.extend([
        "",
        "## Clause de Securite Reglementaire",
        "",
        "- V2.5 ne valide aucune stratégie",
        "- V2.5 ne produit aucun label",
        "- V2.5 ne produit aucun modèle ML",
        "- V2.5 ne produit aucun backtest",
        "- V2.5 ne produit aucun signal de trading",
        "- V2.5 ne produit aucun ordre",
        "- V2.5 n’autorise aucun paper live",
        "- V2.5 n’autorise aucun trading réel",
        "",
        "Le Feature Store V2.5 est conçu et limité à des fins strictes d'analyse historique de données de marché en mode read-only (Data/Research Only).",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print("=== Generating Galapagos V2.5 Causal Feature Store Preview ===")
    manifest = run_feature_store_generation()
    print(f"Status: {manifest['status']}")
    print(f"Run ID: {manifest['feature_run_id']}")
    print(f"Outputs path:")
    for tf in TARGET_TIMEFRAMES:
        print(f"  {tf}: {manifest['outputs'][tf]['path']} ({manifest['outputs'][tf]['rows']} rows)")
    print("==============================================================")
