from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from galapagos.data.public_market.one_year_window import (
    WINDOW_LABEL_V4_2,
    output_path as v4_2_ohlcv_path,
)
from galapagos.data.public_market.one_year_window_validation import validate_one_year_public_market_data_v4_2
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.labels.one_year_window_quality import EXPECTED_ROWS_V4_4, assess_one_year_label_quality
from galapagos.labels.forward_returns import build_forward_labels
from galapagos.labels.registry import HORIZONS, THRESHOLD
from galapagos.labels.schemas import LABEL_COLUMNS_V4_4


VERSION_V4_4 = "V4.4"
LABEL_SCHEMA_VERSION_V4_4 = "V4.4"
TIMEFRAMES_V4_4 = ["1m", "5m", "15m", "1h"]
MANIFEST_PATH_V4_4 = Path("reports/manifests/one_year_label_factory_v4_4_manifest.json")
REPORT_JSON_PATH_V4_4 = Path("reports/labels/one_year_label_factory_v4_4.json")
REPORT_MD_PATH_V4_4 = Path("reports/labels/one_year_label_factory_v4_4.md")
DOC_PATH_V4_4 = Path("docs/one_year_label_factory_v4_4.md")
EXPECTED_LIMITATIONS_V4_4 = [
    "V4.4 produit uniquement des labels forward 1 an separes sur BTCUSDT 2024-01-01 a 2024-12-31 a partir des donnees OHLCV V4.2 validees.",
    "V4.4 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
]


def run_one_year_label_factory_v4_4(root: Path = Path("."), *, validate_inputs: bool = True) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        result = validate_one_year_public_market_data_v4_2(root)
        if not result["passed"]:
            raise RuntimeError(f"V4.2 validation failed before V4.4: {result['errors']}")

    created_at = utc_now_iso()
    label_run_id = f"v4_4_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_ohlcv: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V4_4:
        input_path = v4_2_ohlcv_path(root, timeframe)
        input_frame = read_parquet(input_path)
        input_sha = sha256_file(input_path)
        label_frame = build_forward_labels(
            input_frame,
            input_sha,
            label_run_id,
            label_schema_version=LABEL_SCHEMA_VERSION_V4_4,
        )
        output = output_path(root, timeframe)
        write_parquet(label_frame[LABEL_COLUMNS_V4_4], output)
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
        quality[timeframe] = assess_one_year_label_quality(label_frame, timeframe)
        quality[timeframe]["source_hashes_valid"] = True
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V4_4,
        "status": status,
        "created_at_utc": created_at,
        "label_run_id": label_run_id,
        "input_ohlcv": input_ohlcv,
        "outputs": outputs,
        "label_schema_version": LABEL_SCHEMA_VERSION_V4_4,
        "label_columns": LABEL_COLUMNS_V4_4,
        "horizons": HORIZONS,
        "threshold": THRESHOLD,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V4_4,
    }
    report = _build_report(manifest)
    _write_json(root / MANIFEST_PATH_V4_4, manifest)
    _write_json(root / REPORT_JSON_PATH_V4_4, report)
    markdown = build_one_year_label_factory_markdown_v4_4(report)
    _write_text(root / REPORT_MD_PATH_V4_4, markdown)
    _write_text(root / DOC_PATH_V4_4, markdown)
    return manifest


def output_path(root: Path, timeframe: str) -> Path:
    return (
        root
        / "data/research/v4_4/labels/forward_returns"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={WINDOW_LABEL_V4_2}"
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


def build_one_year_label_factory_markdown_v4_4(report: dict[str, Any]) -> str:
    outputs = "\n".join(
        f"- `{timeframe}` : `{report['outputs'][timeframe]['rows']}` lignes, `{report['outputs'][timeframe]['path']}`"
        for timeframe in TIMEFRAMES_V4_4
    )
    quality_rows = "\n".join(
        f"- `{timeframe}` : tail rows `{payload['tail_rows']}`, h1 `{payload['valid_counts_by_horizon']['h1']}`, h3 `{payload['valid_counts_by_horizon']['h3']}`, h5 `{payload['valid_counts_by_horizon']['h5']}`, erreurs `{len(payload['errors'])}`"
        for timeframe, payload in report["quality"].items()
    )
    label_columns = "\n".join(f"- `{column}`" for column in LABEL_COLUMNS_V4_4)
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    return f"""# One-Year Clean Forward Label Factory V4.4

## Objectif

V4.4 construit uniquement des labels forward 1 an sur BTCUSDT du 2024-01-01 au 2024-12-31, a partir des OHLCV V4.2 valides.

## Inputs

- Source : OHLCV V4.2 `data/research/v4_2/silver/ohlcv`
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

- Les labels regardent le futur uniquement dans la couche labels separee V4.4.
- Aucune jointure features + labels n'est produite.
- Aucun label n'est ecrit dans `data/research/v4_3/features`.
- Aucun dataset ML V4.4 n'est produit.
- Les dernieres lignes sans futur suffisant restent marquees invalides par horizon et `tail_row = true`.

## Qualite par timeframe

{quality_rows}

## Limitations

{limitations}

## Securite

- V4.4 ne valide aucune stratégie
- V4.4 ne produit aucun dataset ML
- V4.4 ne produit aucun modèle ML
- V4.4 ne produit aucun backtest
- V4.4 ne produit aucun signal de trading
- V4.4 ne produit aucun ordre
- V4.4 n’autorise aucun paper live
- V4.4 n’autorise aucun trading réel

V4.4 reste `pending_external_audit`.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
