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
from galapagos.labels.expanded_window_quality import EXPECTED_ROWS_V3_7, assess_expanded_label_quality
from galapagos.labels.forward_returns import build_forward_labels
from galapagos.labels.registry import HORIZONS, THRESHOLD
from galapagos.labels.schemas import LABEL_COLUMNS_V3_7


VERSION_V3_7 = "V3.7"
LABEL_SCHEMA_VERSION_V3_7 = "V3.7"
TIMEFRAMES_V3_7 = ["1m", "5m", "15m", "1h"]
MANIFEST_PATH_V3_7 = Path("reports/manifests/expanded_label_factory_v3_7_manifest.json")
REPORT_JSON_PATH_V3_7 = Path("reports/labels/expanded_label_factory_v3_7.json")
REPORT_MD_PATH_V3_7 = Path("reports/labels/expanded_label_factory_v3_7.md")
DOC_PATH_V3_7 = Path("docs/expanded_label_factory_v3_7.md")
EXPECTED_LIMITATIONS_V3_7 = [
    "V3.7 produit uniquement des labels forward 90 jours separes sur BTCUSDT 2024-01-01 a 2024-03-30 a partir des donnees OHLCV V3.5 validees.",
    "V3.7 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]


def run_expanded_label_factory_v3_7(root: Path = Path("."), *, validate_inputs: bool = True) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        result = validate_expanded_public_market_data_v3_5(root)
        if not result["passed"]:
            raise RuntimeError(f"V3.5 validation failed before V3.7: {result['errors']}")

    created_at = utc_now_iso()
    label_run_id = f"v3_7_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_ohlcv: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V3_7:
        input_path = v3_5_ohlcv_path(root, timeframe)
        input_frame = read_parquet(input_path)
        input_sha = sha256_file(input_path)
        label_frame = build_forward_labels(
            input_frame,
            input_sha,
            label_run_id,
            label_schema_version=LABEL_SCHEMA_VERSION_V3_7,
        )
        output = output_path(root, timeframe)
        write_parquet(label_frame[LABEL_COLUMNS_V3_7], output)
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
        quality[timeframe] = assess_expanded_label_quality(label_frame, timeframe)
        quality[timeframe]["source_hashes_valid"] = True
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V3_7,
        "status": status,
        "created_at_utc": created_at,
        "label_run_id": label_run_id,
        "input_ohlcv": input_ohlcv,
        "outputs": outputs,
        "label_schema_version": LABEL_SCHEMA_VERSION_V3_7,
        "label_columns": LABEL_COLUMNS_V3_7,
        "horizons": HORIZONS,
        "threshold": THRESHOLD,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V3_7,
    }
    report = _build_report(manifest)
    _write_json(root / MANIFEST_PATH_V3_7, manifest)
    _write_json(root / REPORT_JSON_PATH_V3_7, report)
    markdown = build_expanded_label_factory_markdown_v3_7(report)
    _write_text(root / REPORT_MD_PATH_V3_7, markdown)
    _write_text(root / DOC_PATH_V3_7, markdown)
    return manifest


def output_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v3_7/labels/forward_returns"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_LABEL_V3_5}"
        / "labels.parquet"
    )


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


def build_expanded_label_factory_markdown_v3_7(report: dict[str, Any]) -> str:
    outputs = "\n".join(
        f"- `{timeframe}` : `{report['outputs'][timeframe]['rows']}` lignes, `{report['outputs'][timeframe]['path']}`"
        for timeframe in TIMEFRAMES_V3_7
    )
    quality_rows = "\n".join(
        f"- `{timeframe}` : tail rows `{payload['tail_rows']}`, h1 `{payload['valid_counts_by_horizon']['h1']}`, h3 `{payload['valid_counts_by_horizon']['h3']}`, h5 `{payload['valid_counts_by_horizon']['h5']}`, erreurs `{len(payload['errors'])}`"
        for timeframe, payload in report["quality"].items()
    )
    label_columns = "\n".join(f"- `{column}`" for column in LABEL_COLUMNS_V3_7)
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    return f"""# Expanded Clean Forward Label Factory V3.7

## Objectif

V3.7 construit uniquement des labels forward 90 jours sur BTCUSDT du 2024-01-01 au 2024-03-30, a partir des OHLCV V3.5 valides.

## Inputs

- Source : OHLCV V3.5 `data/research/v3_5/silver/ohlcv`
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
- `label_available_ts` est strictement posterieur a `decision_ts` pour les lignes avec au moins un label valide.

## Colonnes

{label_columns}

## Regles anti-leakage

- Les labels regardent le futur uniquement dans la couche labels separee V3.7.
- Aucune jointure features + labels n'est produite.
- Aucun label n'est ecrit dans `data/research/v3_6/features`.
- Aucun dataset ML V3.7 n'est produit.
- Les dernieres lignes sans futur suffisant restent marquees invalides par horizon et `tail_row = true`.

## Qualite par timeframe

{quality_rows}

## Limitations

{limitations}

## Securite

- V3.7 ne valide aucune stratégie
- V3.7 ne produit aucun dataset ML
- V3.7 ne produit aucun modèle ML
- V3.7 ne produit aucun backtest
- V3.7 ne produit aucun signal de trading
- V3.7 ne produit aucun ordre
- V3.7 n’autorise aucun paper live
- V3.7 n’autorise aucun trading réel

V3.7 reste `pending_external_audit`.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
