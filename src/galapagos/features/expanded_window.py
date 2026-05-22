from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from galapagos.data.public_market.expanded_window import (
    WINDOW_LABEL_V3_5,
    output_path as v3_5_ohlcv_path,
)
from galapagos.data.public_market.expanded_window_validation import validate_expanded_public_market_data_v3_5
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.features.causal_ohlcv import build_causal_features
from galapagos.features.expanded_window_quality import EXPECTED_ROWS_V3_6, assess_expanded_feature_quality
from galapagos.features.schemas import FEATURE_COLUMNS_V3_6


VERSION_V3_6 = "V3.6"
FEATURE_SCHEMA_VERSION_V3_6 = "V3.6"
TIMEFRAMES_V3_6 = ["1m", "5m", "15m", "1h"]
MANIFEST_PATH_V3_6 = Path("reports/manifests/expanded_causal_feature_store_v3_6_manifest.json")
REPORT_JSON_PATH_V3_6 = Path("reports/features/expanded_causal_feature_store_v3_6.json")
REPORT_MD_PATH_V3_6 = Path("reports/features/expanded_causal_feature_store_v3_6.md")
DOC_PATH_V3_6 = Path("docs/expanded_causal_feature_store_v3_6.md")
EXPECTED_LIMITATIONS_V3_6 = [
    "V3.6 produit uniquement des features OHLCV causales sur BTCUSDT 2024-01-01 a 2024-03-30 a partir des donnees V3.5 validees.",
    "V3.6 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]


def run_expanded_causal_feature_store_v3_6(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        result = validate_expanded_public_market_data_v3_5(root)
        if not result["passed"]:
            raise RuntimeError(f"V3.5 validation failed before V3.6: {result['errors']}")

    created_at = utc_now_iso()
    feature_run_id = f"v3_6_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_ohlcv: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V3_6:
        input_path = v3_5_ohlcv_path(root, timeframe)
        input_frame = read_parquet(input_path)
        input_sha = sha256_file(input_path)
        feature_frame = build_causal_features(
            input_frame,
            input_sha,
            feature_run_id,
            feature_schema_version=FEATURE_SCHEMA_VERSION_V3_6,
        )
        output = output_path(root, timeframe)
        write_parquet(feature_frame[FEATURE_COLUMNS_V3_6], output)

        input_ohlcv[timeframe] = {
            "path": str(input_path.relative_to(root)),
            "sha256": input_sha,
            "rows": int(len(input_frame)),
        }
        outputs[timeframe] = {
            "path": str(output.relative_to(root)),
            "sha256": sha256_file(output),
            "bytes": output.stat().st_size,
            "rows": int(len(feature_frame)),
            "format": "parquet",
        }
        quality[timeframe] = assess_expanded_feature_quality(feature_frame, timeframe)
        quality[timeframe]["source_hashes_valid"] = True
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V3_6,
        "status": status,
        "created_at_utc": created_at,
        "feature_run_id": feature_run_id,
        "input_ohlcv": input_ohlcv,
        "outputs": outputs,
        "feature_schema_version": FEATURE_SCHEMA_VERSION_V3_6,
        "feature_columns": FEATURE_COLUMNS_V3_6,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V3_6,
    }
    report = _build_report(manifest)
    _write_json(root / MANIFEST_PATH_V3_6, manifest)
    _write_json(root / REPORT_JSON_PATH_V3_6, report)
    markdown = build_expanded_causal_feature_store_markdown_v3_6(report)
    _write_text(root / REPORT_MD_PATH_V3_6, markdown)
    _write_text(root / DOC_PATH_V3_6, markdown)
    return manifest


def output_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_6/features/ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_LABEL_V3_5}"
        / "features.parquet"
    )


def _build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "feature_run_id": manifest["feature_run_id"],
        "input_ohlcv": manifest["input_ohlcv"],
        "outputs": manifest["outputs"],
        "feature_schema_version": manifest["feature_schema_version"],
        "feature_columns": manifest["feature_columns"],
        "quality": manifest["quality"],
        "safety": manifest["safety"],
        "limitations": manifest["limitations"],
    }


def _safety() -> dict[str, bool]:
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_expanded_causal_feature_store_markdown_v3_6(report: dict[str, Any]) -> str:
    rows = "\n".join(
        f"- `{timeframe}` : `{report['outputs'][timeframe]['rows']}` lignes, `{report['outputs'][timeframe]['path']}`"
        for timeframe in TIMEFRAMES_V3_6
    )
    quality_rows = "\n".join(
        f"- `{timeframe}` : warmup `{payload['warmup_rows']}`, lignes apres warmup `{payload['rows_after_warmup']}`, erreurs `{len(payload['errors'])}`"
        for timeframe, payload in report["quality"].items()
    )
    feature_list = "\n".join(f"- `{column}`" for column in FEATURE_COLUMNS_V3_6)
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    return f"""# Expanded Causal Feature Store V3.6

## Objectif

V3.6 construit uniquement un feature store OHLCV causal 90 jours sur BTCUSDT du 2024-01-01 au 2024-03-30, a partir des OHLCV V3.5 valides.

## Inputs

- Source : OHLCV V3.5 `data/research/v3_5/silver/ohlcv`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `{report['feature_run_id']}`

## Outputs

{rows}

## Features calculees

{feature_list}

## Regles causales

- Les lags et rolling windows utilisent uniquement les observations passees ou courantes.
- Aucun `future_return`, label, target, prediction, signal, order, pnl ou backtest n'est produit.
- `feature_available_ts = available_ts` pour cette preview.
- `decision_ts >= feature_available_ts` est verifie physiquement.

## Warmup

Les 30 premieres lignes de chaque timeframe restent marquees `warmup_row = true` lorsque les lags ou rolling windows critiques ne sont pas encore disponibles. Les NaN de warmup ne sont pas remplis artificiellement.

## Qualite par timeframe

{quality_rows}

## Limitations

{limitations}

## Securite

- V3.6 ne valide aucune stratégie
- V3.6 ne produit aucun label
- V3.6 ne produit aucun dataset ML
- V3.6 ne produit aucun modèle ML
- V3.6 ne produit aucun backtest
- V3.6 ne produit aucun signal de trading
- V3.6 ne produit aucun ordre
- V3.6 n’autorise aucun paper live
- V3.6 n’autorise aucun trading réel

V3.6 reste `pending_external_audit`.
"""
