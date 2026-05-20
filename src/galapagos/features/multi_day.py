from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from galapagos.data.public_market.multi_day import WINDOW_LABEL, output_path as v2_9_ohlcv_path
from galapagos.data.public_market.multi_day_validation import validate_multi_day_public_market_data_v2_9
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.validation import validate_offline_supervised_dataset_v2_7
from galapagos.features.causal_ohlcv import build_causal_features
from galapagos.features.multi_day_quality import EXPECTED_ROWS_V3_0, assess_multi_day_feature_quality
from galapagos.features.schemas import FEATURE_COLUMNS_V3_0
from galapagos.features.validation import validate_causal_feature_store_v2_5
from galapagos.labels.validation import validate_label_factory_v2_6
from galapagos.ml.validation import validate_offline_ml_research_v2_8
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4


VERSION = "V3.0"
FEATURE_SCHEMA_VERSION = "V3.0"
TIMEFRAMES_V3_0 = ["1m", "5m", "15m", "1h"]
MANIFEST_PATH = Path("reports/manifests/multi_day_causal_feature_store_v3_0_manifest.json")
REPORT_JSON_PATH = Path("reports/features/multi_day_causal_feature_store_v3_0.json")
REPORT_MD_PATH = Path("reports/features/multi_day_causal_feature_store_v3_0.md")
DOC_PATH = Path("docs/multi_day_causal_feature_store_v3_0.md")
EXPECTED_LIMITATIONS_V3_0 = [
    "V3.0 produit uniquement des features OHLCV causales multi-day sur BTCUSDT 2024-01-15 a 2024-01-21 a partir des donnees V2.9 validees.",
    "V3.0 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]


def run_multi_day_causal_feature_store_v3_0(root: Path = Path("."), *, validate_previous_layers: bool = True) -> dict[str, Any]:
    root = root.resolve()
    if validate_previous_layers:
        _validate_previous_layers(root)
    created_at = utc_now_iso()
    feature_run_id = f"v3_0_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_ohlcv: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V3_0:
        input_path = v2_9_ohlcv_path(root, timeframe)
        input_frame = read_parquet(input_path)
        input_sha = sha256_file(input_path)
        feature_frame = build_causal_features(
            input_frame,
            input_sha,
            feature_run_id,
            feature_schema_version=FEATURE_SCHEMA_VERSION,
        )
        output = output_path(root, timeframe)
        write_parquet(feature_frame[FEATURE_COLUMNS_V3_0], output)
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
        quality[timeframe] = assess_multi_day_feature_quality(feature_frame, timeframe)
        quality[timeframe]["source_hashes_valid"] = True
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION,
        "status": status,
        "created_at_utc": created_at,
        "feature_run_id": feature_run_id,
        "input_ohlcv": input_ohlcv,
        "outputs": outputs,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_columns": FEATURE_COLUMNS_V3_0,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V3_0,
    }
    report = _build_report(manifest)
    _write_json(root / MANIFEST_PATH, manifest)
    _write_json(root / REPORT_JSON_PATH, report)
    _write_markdown(root / REPORT_MD_PATH, report)
    _write_markdown(root / DOC_PATH, report)
    return manifest


def output_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_0/features/ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_LABEL}"
        / "features.parquet"
    )


def _validate_previous_layers(root: Path) -> None:
    validators = [
        ("V2.3.1", validate_public_market_ingestion_v2_3),
        ("V2.4.8", validate_ohlcv_resampling_v2_4),
        ("V2.5.2", validate_causal_feature_store_v2_5),
        ("V2.6.2", validate_label_factory_v2_6),
        ("V2.7.2", validate_offline_supervised_dataset_v2_7),
        ("V2.8.4", validate_offline_ml_research_v2_8),
        ("V2.9.1", validate_multi_day_public_market_data_v2_9),
    ]
    for label, validator in validators:
        result = validator(root)
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed before V3.0: {result['errors']}")


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


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    outputs = "\n".join(
        f"- `{timeframe}` : `{report['outputs'][timeframe]['rows']}` lignes, `{report['outputs'][timeframe]['path']}`"
        for timeframe in TIMEFRAMES_V3_0
    )
    quality_rows = "\n".join(
        f"- `{timeframe}` : warmup `{payload['warmup_rows']}`, lignes apres warmup `{payload['rows_after_warmup']}`, erreurs `{len(payload['errors'])}`"
        for timeframe, payload in report["quality"].items()
    )
    feature_list = "\n".join(f"- `{column}`" for column in FEATURE_COLUMNS_V3_0)
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    text = f"""# Multi-Day Causal Feature Store V3.0

## Objectif

V3.0 construit uniquement un feature store OHLCV causal multi-day sur BTCUSDT du 2024-01-15 au 2024-01-21, a partir des OHLCV multi-day V2.9 valides.

## Inputs

- Source : OHLCV V2.9 `data/research/v2_9/silver/ohlcv`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `{report['feature_run_id']}`

## Outputs

{outputs}

## Features calculees

{feature_list}

## Regles causales

- Les lags et rolling windows utilisent uniquement les observations passees ou courantes.
- Aucun `future_return`, label, target, prediction, signal, order, pnl ou backtest n'est produit.
- `feature_available_ts = available_ts` pour cette preview.
- `decision_ts >= feature_available_ts` est verifie physiquement.

## Warmup

Les premieres lignes de chaque timeframe restent marquees `warmup_row = true` lorsque les lags ou rolling windows critiques ne sont pas encore disponibles. Les NaN de warmup ne sont pas remplis artificiellement.

## Qualite par timeframe

{quality_rows}

## Limitations

{limitations}

## Securite

- V3.0 ne valide aucune stratégie
- V3.0 ne produit aucun label
- V3.0 ne produit aucun dataset ML
- V3.0 ne produit aucun modèle ML
- V3.0 ne produit aucun backtest
- V3.0 ne produit aucun signal de trading
- V3.0 ne produit aucun ordre
- V3.0 n’autorise aucun paper live
- V3.0 n’autorise aucun trading réel

V3.0 reste `pending_external_audit`.
"""
    path.write_text(text, encoding="utf-8")
