from __future__ import annotations

import datetime
import json
import uuid
import sys
from pathlib import Path

import _bootstrap
_bootstrap.bootstrap_src_path()

import pandas as pd
import numpy as np

# Prior Validators
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4
from galapagos.features.validation import validate_causal_feature_store_v2_5

# V2.6 labels
from galapagos.labels.schemas import LABEL_COLUMNS_V2_6
from galapagos.labels.registry import (
    VERSION,
    CORRECTION_VERSION,
    LABEL_SCHEMA_VERSION,
    TARGET_TIMEFRAMES,
    HORIZONS,
    THRESHOLD,
    MANIFEST_PATH,
    QUALITY_JSON_PATH,
    QUALITY_MD_PATH,
    get_label_gold_path,
)
from galapagos.labels.forward_returns import build_forward_labels
from galapagos.labels.quality import assess_label_quality
from galapagos.data.public_market.provenance import sha256_file


def run_pipeline_check(root: Path) -> None:
    """Runs V2.3, V2.4 and V2.5 validators to ensure historical pipeline is green."""
    print("=== Step 1: Running Galapagos Pipeline Chain Checks ===")
    
    # 1. Ingestion V2.3
    print("-> Checking Ingestion V2.3.1...")
    res_v2_3 = validate_public_market_ingestion_v2_3(root)
    if not res_v2_3["passed"]:
        print(f"Error: Ingestion V2.3 validator failed: {res_v2_3['errors']}")
        sys.exit(1)
    print("   Ingestion V2.3: PASS")
    
    # 2. Resampling V2.4
    print("-> Checking Resampling V2.4.8...")
    res_v2_4 = validate_ohlcv_resampling_v2_4(root)
    if not res_v2_4["passed"]:
        print(f"Error: Resampling V2.4 validator failed: {res_v2_4['errors']}")
        sys.exit(1)
    print("   Resampling V2.4: PASS")
    
    # 3. Causal Feature Store V2.5
    print("-> Checking Feature Store V2.5.2...")
    res_v2_5 = validate_causal_feature_store_v2_5(root)
    if not res_v2_5["passed"]:
        print(f"Error: Feature Store V2.5 validator failed: {res_v2_5['errors']}")
        sys.exit(1)
    print("   Feature Store V2.5: PASS")
    
    print("=== Pipeline Chain Checks: ALL GREEN ===\n")


def main() -> None:
    root = Path(".")
    
    # 1. Pipeline check
    run_pipeline_check(root)
    
    print("=== Step 2: Generating Galapagos V2.6 Clean Forward Labels ===")
    
    run_id_ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    short_uid = str(uuid.uuid4())[:8]
    label_run_id = f"v2_6_{run_id_ts}_{short_uid}"
    
    input_ohlcv_manifest = {}
    outputs_manifest = {}
    quality_manifest = {}
    
    # Process each timeframe
    for tf in TARGET_TIMEFRAMES:
        print(f"-> Processing timeframe: {tf}...")
        
        # Resolve silver ohlcv path
        silver_path = root / f"data/silver/market_data/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={tf}/year=2024/month=01/part-2024-01-15.parquet"
        if not silver_path.exists():
            print(f"Error: Silver Parquet not found for {tf} at {silver_path}")
            sys.exit(1)
            
        silver_sha256 = sha256_file(silver_path)
        silver_bytes = silver_path.stat().st_size
        
        # Load OHLCV data
        ohlcv_df = pd.read_parquet(silver_path)
        ohlcv_rows = len(ohlcv_df)
        
        input_ohlcv_manifest[tf] = {
            "path": str(silver_path.relative_to(root) if silver_path.is_absolute() else silver_path),
            "sha256": silver_sha256,
            "rows": ohlcv_rows,
        }
        
        # Build labels
        labels_df = build_forward_labels(ohlcv_df, silver_sha256, label_run_id)
        
        # Write output Parquet Gold
        gold_path = get_label_gold_path(root, tf)
        gold_path.parent.mkdir(parents=True, exist_ok=True)
        labels_df.to_parquet(gold_path, index=False)
        
        gold_sha256 = sha256_file(gold_path)
        gold_bytes = gold_path.stat().st_size
        gold_rows = len(labels_df)
        
        outputs_manifest[tf] = {
            "path": str(gold_path.relative_to(root) if gold_path.is_absolute() else gold_path),
            "sha256": gold_sha256,
            "bytes": gold_bytes,
            "rows": gold_rows,
            "format": "parquet",
        }
        
        # Compute quality statistics
        stats = assess_label_quality(labels_df, ohlcv_rows)
        quality_manifest[tf] = stats
        
        print(f"   Written Parquet Gold: {gold_path} ({gold_rows} rows)")
        
    safety = {
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "ml_enabled": False,
        "labels_enabled": True,
        "backtest_enabled": False
    }
    
    # 2. Build Manifest
    print("\n-> Building manifest...")
    manifest = {
        "version": "V2.6",
        "correction_version": CORRECTION_VERSION,
        "status": "PASS",
        "created_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "label_run_id": label_run_id,
        "input_ohlcv": input_ohlcv_manifest,
        "outputs": outputs_manifest,
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "label_columns": LABEL_COLUMNS_V2_6,
        "horizons": HORIZONS,
        "threshold": THRESHOLD,
        "quality": quality_manifest,
        "safety": safety,
        "limitations": [
            "V2.6 produit uniquement des labels forward separes sur BTCUSDT 2024-01-15 a partir des donnees OHLCV V2.4 validees.",
            "V2.6 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre."
        ]
    }
    
    # Ensure reports/dirs exist
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save Manifest
    with open(root / MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"   Manifest written: {MANIFEST_PATH}")
    
    # Save JSON Report
    with open(root / QUALITY_JSON_PATH, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"   JSON Report written: {QUALITY_JSON_PATH}")
    
    # 3. Save Markdown Report
    print("-> Generating Markdown report...")
    md_report = f"""# Rapport de Qualité — Galapagos V2.6 Clean Forward Label Factory

Ce document fournit une analyse exhaustive de la qualité physique, structurelle et causale des labels forward générés par la version **V2.6**. 

---

## 1. Objectif technique
La version V2.6 établit un processus rigoureux de labellisation forward, séparé à 100% du stockage des caractéristiques (features) de la V2.5.2. Ces labels sont calculés à partir de la série temporelle d'OHLCV validée V2.4.

---

## 2. Intrants et Extrants
- **Données sources (Input) :** Série OHLCV Parquet Silver V2.4.
- **Labels générés (Output) :** Fichiers Parquet Gold sous `data/gold/labels/forward_returns/`.

---

## 3. Définition des horizons et classification
- **Horizons :** Horizons de projection de barres $h \\in {HORIZONS}$
- **Seuil (Threshold) :** Classification catégorielle avec seuil fixe de `{THRESHOLD}`.
- **Formule returns :** 
  - $R_t^s = \\frac{{\\text{{close}}_{{t+h}}}}{{\\text{{close}}_t}} - 1.0$ (Simple Return)
  - $R_t^l = \\ln\\left(\\frac{{\\text{{close}}_{{t+h}}}}{{\\text{{close}}_t}}\\right)$ (Log Return)
- **Classification UP/DOWN/FLAT :**
  - `"UP"` si $R_t^l > {THRESHOLD}$
  - `"DOWN"` si $R_t^l < -{THRESHOLD}$
  - `"FLAT"` sinon.

---

## 4. Règles strictes de non-leakage et de causalité
- **Séparation causale :** Pour toute observation avec labels valides, l'horodatage de disponibilité de ces labels (`label_available_ts`) est garanti strictement supérieur à la date de décision (`decision_ts`).
- **Nullification de queue (Tail Rows) :** Les dernières $h$ lignes de chaque timeframe ne disposant pas d'un horizon futur suffisant sont explicitement marquées avec `label_valid = false` et leurs valeurs sont nulles (None/NaN) pour interdire toute extrapolation.
- **Isolation :** Aucun label n'est écrit ou fusionné dans le dossier des features Gold. Aucun fichier de dataset ML fusionné n'est créé.

---

## 5. Synthèse de la qualité par timeframe
"""

    for tf in TARGET_TIMEFRAMES:
        tf_stats = quality_manifest[tf]
        md_report += f"""
### Timeframe : {tf}
- **Lignes totales :** {tf_stats['rows']}
- **Lignes attendues :** {tf_stats['expected_rows']}
- **Doublons détectés :** {tf_stats['duplicate_rows']}
- **Lignes de queue (Tail Rows) :** {tf_stats['tail_rows']}
- **Séparation causale validée :** {"Oui" if tf_stats['causal_separation_guard_passed'] else "Non (Erreur détectée)"}
- **Présence de colonnes interdites :** {"Non (PASS)" if not tf_stats['forbidden_columns_present'] else "Oui (Rejet)"}
- **Validité des horodatages de queue :** {"Oui" if tf_stats['label_end_ts_valid'] else "Invalide"}
- **Nombre de labels valides par horizon :**
  - Horizon 1 : {tf_stats['valid_counts_by_horizon']['h1']} valides
  - Horizon 3 : {tf_stats['valid_counts_by_horizon']['h3']} valides
  - Horizon 5 : {tf_stats['valid_counts_by_horizon']['h5']} valides
"""

    md_report += f"""
---

## 6. Sécurité et limitations de conformité
- **public_read_only :** {safety["public_read_only"]}
- **orders_enabled :** {safety["orders_enabled"]}
- **trading_enabled :** {safety["trading_enabled"]}
- **ml_enabled :** {safety["ml_enabled"]}
- **labels_enabled :** {safety["labels_enabled"]}
- **backtest_enabled :** {safety["backtest_enabled"]}
- **paper_live_enabled :** {safety["paper_live_enabled"]}

> [!IMPORTANT]
> - V2.6 produit uniquement des labels forward separes sur BTCUSDT 2024-01-15 a partir des donnees OHLCV V2.4 validees.
> - V2.6 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.
> - V2.6 n'autorise aucun paper live et aucun trading reel.
"""

    with open(root / QUALITY_MD_PATH, "w") as f:
        f.write(md_report)
    print(f"   Markdown Report written: {QUALITY_MD_PATH}")
    
    print("==============================================================\n")


if __name__ == "__main__":
    main()
