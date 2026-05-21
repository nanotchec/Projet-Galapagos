from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from galapagos.data.public_market.multi_day import output_path as v2_9_ohlcv_path
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.labels.forward_returns import build_forward_labels
from galapagos.labels.multi_day_config import (
    DOC_PATH,
    EXPECTED_LIMITATIONS_V3_1,
    LABEL_SCHEMA_VERSION,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    TIMEFRAMES_V3_1,
    VERSION,
    output_path,
)
from galapagos.labels.multi_day_quality import EXPECTED_ROWS_V3_1, assess_multi_day_label_quality
from galapagos.labels.registry import HORIZONS, THRESHOLD
from galapagos.labels.schemas import LABEL_COLUMNS_V3_1


def run_multi_day_label_factory_v3_1(root: Path = Path("."), *, validate_previous_layers: bool = True) -> dict[str, Any]:
    root = root.resolve()
    if validate_previous_layers:
        _validate_previous_layers(root)
    created_at = utc_now_iso()
    label_run_id = f"v3_1_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_ohlcv: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V3_1:
        input_path = v2_9_ohlcv_path(root, timeframe)
        input_frame = read_parquet(input_path)
        input_sha = sha256_file(input_path)
        label_frame = build_forward_labels(
            input_frame,
            input_sha,
            label_run_id,
            label_schema_version=LABEL_SCHEMA_VERSION,
        )
        output = output_path(root, timeframe)
        write_parquet(label_frame[LABEL_COLUMNS_V3_1], output)
        input_ohlcv[timeframe] = {
            "path": str(input_path.relative_to(root)),
            "sha256": input_sha,
            "rows": int(len(input_frame)),
        }
        outputs[timeframe] = {
            "path": str(output.relative_to(root)),
            "sha256": sha256_file(output),
            "bytes": output.stat().st_size,
            "rows": int(len(label_frame)),
            "format": "parquet",
        }
        quality[timeframe] = assess_multi_day_label_quality(label_frame, timeframe)
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION,
        "status": status,
        "created_at_utc": created_at,
        "label_run_id": label_run_id,
        "input_ohlcv": input_ohlcv,
        "outputs": outputs,
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "label_columns": LABEL_COLUMNS_V3_1,
        "horizons": HORIZONS,
        "threshold": THRESHOLD,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V3_1,
    }
    report = _build_report(manifest)
    _write_json(root / MANIFEST_PATH, manifest)
    _write_json(root / REPORT_JSON_PATH, report)
    _write_markdown(root / REPORT_MD_PATH, report)
    _write_markdown(root / DOC_PATH, report)
    return manifest


def _validate_previous_layers(root: Path) -> None:
    from galapagos.data.public_market.multi_day_validation import validate_multi_day_public_market_data_v2_9
    from galapagos.datasets.validation import validate_offline_supervised_dataset_v2_7
    from galapagos.features.multi_day_validation import validate_multi_day_causal_feature_store_v3_0
    from galapagos.features.validation import validate_causal_feature_store_v2_5
    from galapagos.labels.validation import validate_label_factory_v2_6
    from galapagos.ml.validation import validate_offline_ml_research_v2_8
    from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
    from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4

    validators = [
        ("V2.3.1", validate_public_market_ingestion_v2_3),
        ("V2.4.8", validate_ohlcv_resampling_v2_4),
        ("V2.5.2", validate_causal_feature_store_v2_5),
        ("V2.6.2", validate_label_factory_v2_6),
        ("V2.7.2", validate_offline_supervised_dataset_v2_7),
        ("V2.8.4", validate_offline_ml_research_v2_8),
        ("V2.9.1", validate_multi_day_public_market_data_v2_9),
        ("V3.0", validate_multi_day_causal_feature_store_v3_0),
    ]
    for label, validator in validators:
        result = validator(root)
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed before V3.1: {result['errors']}")


def _build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "label_run_id": manifest["label_run_id"],
        "input_ohlcv": manifest["input_ohlcv"],
        "outputs": manifest["outputs"],
        "label_schema_version": manifest["label_schema_version"],
        "label_columns": manifest["label_columns"],
        "horizons": manifest["horizons"],
        "threshold": manifest["threshold"],
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
        "labels_enabled": True,
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
        for timeframe in TIMEFRAMES_V3_1
    )
    quality_rows = "\n".join(
        f"- `{timeframe}` : tail rows `{payload['tail_rows']}`, h1 `{payload['valid_counts_by_horizon']['h1']}`, h3 `{payload['valid_counts_by_horizon']['h3']}`, h5 `{payload['valid_counts_by_horizon']['h5']}`, erreurs `{len(payload['errors'])}`"
        for timeframe, payload in report["quality"].items()
    )
    label_list = "\n".join(f"- `{column}`" for column in LABEL_COLUMNS_V3_1)
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    text = f"""# Multi-Day Clean Forward Label Factory V3.1

## Objectif

V3.1 construit uniquement des labels forward multi-day sur BTCUSDT du 2024-01-15 au 2024-01-21, a partir des OHLCV multi-day V2.9 valides.

## Correction V3.1.5

V3.1.5 est une correction smoke-only. V3.1.4 a été refusée en strict uniquement parce que le smoke écrivait ses logs dans le root extrait du ZIP, polluant les validateurs suivants.

V3.1.5 conserve les artefacts fonctionnels V3.1 : mêmes labels, mêmes horizons `[1, 3, 5]`, même threshold `0.0005`, mêmes row counts `10080 / 2016 / 672 / 168`, aucune jointure features + labels et aucun dataset ML.

## Inputs

- Source : OHLCV V2.9 `data/research/v2_9/silver/ohlcv`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `{report['label_run_id']}`

## Outputs

{outputs}

## Horizons et threshold

- Horizons : `{report['horizons']}`
- Threshold fixe : `{report['threshold']}`

## Definition des labels

- `future_close_h` = `close.shift(-h)`.
- `future_simple_return_h` = `future_close_h / close - 1`.
- `future_log_return_h` = `log(future_close_h / close)`.
- `direction_h` vaut `1`, `-1` ou `0` selon le signe du log return.
- `up_down_flat_h` vaut `UP`, `DOWN` ou `FLAT` avec le threshold fixe.

## Colonnes

{label_list}

## Regles anti-leakage

- Les labels regardent le futur uniquement dans la couche labels separee V3.1.
- Aucune jointure features + labels n'est produite.
- Aucun label n'est ecrit dans `data/research/v3_0/features`.
- `label_available_ts > decision_ts` est verifie pour les lignes avec au moins un horizon valide.
- Les dernieres lignes sans futur suffisant restent marquees invalides par horizon et `tail_row = true`.

## Qualite par timeframe

{quality_rows}

## Limitations

{limitations}

## Securite

- V3.1 ne valide aucune stratégie
- V3.1 ne produit aucun dataset ML
- V3.1 ne produit aucun modèle ML
- V3.1 ne produit aucun backtest
- V3.1 ne produit aucun signal de trading
- V3.1 ne produit aucun ordre
- V3.1 n’autorise aucun paper live
- V3.1 n’autorise aucun trading réel

V3.1.5 reste `pending_external_audit`.
"""
    path.write_text(text, encoding="utf-8")
