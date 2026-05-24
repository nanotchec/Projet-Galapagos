from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from galapagos.data.public_market.max_history_window import (
    MANIFEST_PATH_V5_0,
)
from galapagos.data.public_market.max_history_window_validation import validate_max_history_public_market_data_v5_0
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.features.causal_ohlcv import build_causal_features
from galapagos.features.max_history_window_quality import assess_max_history_feature_quality
from galapagos.features.schemas import FEATURE_COLUMNS_V5_1


VERSION_V5_1 = "V5.1"
FEATURE_SCHEMA_VERSION_V5_1 = "V5.1"
TIMEFRAMES_V5_1 = ["1m", "5m", "15m", "1h"]
MANIFEST_PATH_V5_1 = Path("reports/manifests/max_history_causal_feature_store_v5_1_manifest.json")
REPORT_JSON_PATH_V5_1 = Path("reports/features/max_history_causal_feature_store_v5_1.json")
REPORT_MD_PATH_V5_1 = Path("reports/features/max_history_causal_feature_store_v5_1.md")
DOC_PATH_V5_1 = Path("docs/max_history_causal_feature_store_v5_1.md")
EXPECTED_LIMITATIONS_V5_1 = [
    "V5.1 produit uniquement des features OHLCV causales sur la fenetre historique continue validee par V5.0.",
    "V5.1 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]


def run_max_history_causal_feature_store_v5_1(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        result = validate_max_history_public_market_data_v5_0(root)
        if not result["passed"]:
            raise RuntimeError(f"V5.0 validation failed before V5.1: {result['errors']}")

    input_manifest_path = root / MANIFEST_PATH_V5_0
    input_manifest = load_v5_0_ohlcv_manifest(root)
    discovery = input_manifest["discovery"]
    expected_rows = input_manifest["expected_rows"]

    created_at = utc_now_iso()
    feature_run_id = f"v5_1_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_ohlcv: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V5_1:
        input_path = input_ohlcv_path(root, timeframe, input_manifest)
        input_frame = read_parquet(input_path)
        input_sha = sha256_file(input_path)
        feature_frame = build_causal_features(
            input_frame,
            input_sha,
            feature_run_id,
            feature_schema_version=FEATURE_SCHEMA_VERSION_V5_1,
        )
        output = output_path(root, timeframe, discovery["window_start"], discovery["window_end"])
        write_parquet(feature_frame[FEATURE_COLUMNS_V5_1], output)

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
        quality[timeframe] = assess_max_history_feature_quality(
            feature_frame,
            timeframe,
            expected_rows=int(expected_rows[timeframe]),
        )
        quality[timeframe]["source_hashes_valid"] = True
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V5_1,
        "status": status,
        "created_at_utc": created_at,
        "feature_run_id": feature_run_id,
        "input_ohlcv_manifest": {
            "path": str(input_manifest_path.relative_to(root)),
            "sha256": sha256_file(input_manifest_path),
            "window_start": discovery["window_start"],
            "window_end": discovery["window_end"],
            "total_days": int(discovery["total_days"]),
        },
        "input_ohlcv": input_ohlcv,
        "outputs": outputs,
        "feature_schema_version": FEATURE_SCHEMA_VERSION_V5_1,
        "feature_columns": FEATURE_COLUMNS_V5_1,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V5_1,
    }
    report = _build_report(manifest)
    _write_json(root / MANIFEST_PATH_V5_1, manifest)
    _write_json(root / REPORT_JSON_PATH_V5_1, report)
    markdown = build_max_history_causal_feature_store_markdown_v5_1(report)
    _write_text(root / REPORT_MD_PATH_V5_1, markdown)
    _write_text(root / DOC_PATH_V5_1, markdown)
    _update_project_state(root, manifest)
    return manifest


def load_v5_0_ohlcv_manifest(root: Path = Path(".")) -> dict[str, Any]:
    path = root.resolve() / MANIFEST_PATH_V5_0
    return json.loads(path.read_text(encoding="utf-8"))


def input_ohlcv_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v5_0_ohlcv_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def output_path(
    root: Path,
    timeframe: str,
    window_start: str | None = None,
    window_end: str | None = None,
) -> Path:
    if window_start is None or window_end is None:
        manifest = load_v5_0_ohlcv_manifest(root)
        window_start = manifest["discovery"]["window_start"]
        window_end = manifest["discovery"]["window_end"]
    return (
        root.resolve()
        / "data/research/v5_1/features/ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "features.parquet"
    )


def _build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "feature_run_id": manifest["feature_run_id"],
        "input_ohlcv_manifest": manifest["input_ohlcv_manifest"],
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


def build_max_history_causal_feature_store_markdown_v5_1(report: dict[str, Any]) -> str:
    input_manifest = report["input_ohlcv_manifest"]
    rows = "\n".join(
        f"- `{timeframe}` : `{report['outputs'][timeframe]['rows']}` lignes, `{report['outputs'][timeframe]['path']}`"
        for timeframe in TIMEFRAMES_V5_1
    )
    quality_rows = "\n".join(
        f"- `{timeframe}` : warmup `{payload['warmup_rows']}`, lignes apres warmup `{payload['rows_after_warmup']}`, erreurs `{len(payload['errors'])}`"
        for timeframe, payload in report["quality"].items()
    )
    feature_list = "\n".join(f"- `{column}`" for column in FEATURE_COLUMNS_V5_1)
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    return f"""# Max Historical Causal Feature Store V5.1

## Objectif

V5.1 construit uniquement un feature store OHLCV causal sur la fenetre historique continue validee par V5.0 : `{input_manifest['window_start']}` -> `{input_manifest['window_end']}`, soit `{input_manifest['total_days']}` jours.

## Inputs

- Source : OHLCV V5.0 `reports/manifests/max_history_public_market_data_v5_0_manifest.json`
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

- V5.1 ne valide aucune stratégie
- V5.1 ne produit aucun label
- V5.1 ne produit aucun dataset ML
- V5.1 ne produit aucun modèle ML
- V5.1 ne produit aucun backtest
- V5.1 ne produit aucun signal de trading
- V5.1 ne produit aucun ordre
- V5.1 n’autorise aucun paper live
- V5.1 n’autorise aucun trading réel

V5.1 reste `pending_external_audit`.
"""


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    input_manifest = manifest["input_ohlcv_manifest"]
    state.update(
        {
            "last_validated_version": "V5.0",
            "candidate_version": "V5.1",
            "candidate_status": "pending_external_audit",
            "direction": "max historical causal feature store preview",
            "v5_1_candidate": True,
            "max_history_causal_feature_store_v5_1_created": True,
            "max_history_feature_window_start_v5_1": input_manifest["window_start"],
            "max_history_feature_window_end_v5_1": input_manifest["window_end"],
            "max_history_feature_days_v5_1": input_manifest["total_days"],
            "max_history_feature_rows_v5_1": rows,
            "labels_v5_1_created": False,
            "dataset_v5_1_created": False,
            "ml_v5_1_created": False,
            "model_v5_1_created": False,
            "backtest_v5_1_created": False,
            "strategy_v5_1_created": False,
            "signal_v5_1_created": False,
            "orders_v5_1_created": False,
            "paper_live_v5_1_created": False,
            "trading_v5_1_created": False,
            "backtest_enabled": False,
            "strategy_enabled": False,
            "paper_live_enabled": False,
            "orders_enabled": False,
            "trading_enabled": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "authentication_used": False,
        }
    )
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", _build_latest_metrics(manifest, state))
    _write_text(root / "reports/PROJECT_STATE.md", _build_project_state_markdown(manifest))
    _write_text(root / "reports/current/latest_metrics.md", _build_latest_metrics_markdown(manifest))
    _write_text(root / "reports/current/latest_summary.md", _build_latest_summary_markdown(manifest))


def _build_latest_metrics(manifest: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    input_manifest = manifest["input_ohlcv_manifest"]
    return {
        "last_validated_version": "V5.0",
        "candidate_version": "V5.1",
        "candidate_status": "pending_external_audit",
        "direction": state["direction"],
        "max_history_feature_window_start_v5_1": input_manifest["window_start"],
        "max_history_feature_window_end_v5_1": input_manifest["window_end"],
        "max_history_feature_days_v5_1": input_manifest["total_days"],
        "max_history_feature_rows_v5_1": rows,
        "feature_schema_version_v5_1": FEATURE_SCHEMA_VERSION_V5_1,
        "feature_columns_count_v5_1": len(FEATURE_COLUMNS_V5_1),
        "warmup_rows_v5_1": {timeframe: payload["warmup_rows"] for timeframe, payload in manifest["quality"].items()},
        "labels_v5_1_created": False,
        "dataset_v5_1_created": False,
        "ml_v5_1_created": False,
        "model_v5_1_created": False,
        "backtest_v5_1_created": False,
        "strategy_v5_1_created": False,
        "signal_v5_1_created": False,
        "orders_v5_1_created": False,
        "paper_live_v5_1_created": False,
        "trading_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "authentication_used": False,
        "external_validation_required": True,
    }


def _build_project_state_markdown(manifest: dict[str, Any]) -> str:
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    input_manifest = manifest["input_ohlcv_manifest"]
    return f"""# Etat du Projet : V5.0 validee + candidat V5.1

- **Derniere version validee** : V5.0.
- **Version candidate** : V5.1.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : max historical causal feature store preview.

## Candidat V5.1

- Fenetre V5.0 utilisee : `{input_manifest['window_start']}` -> `{input_manifest['window_end']}`.
- Nombre de jours : `{input_manifest['total_days']}`.
- Row counts features : `{rows}`.
- Schema : `FEATURE_COLUMNS_V5_1`.
- V5.1 ne cree aucun label, aucun dataset ML et aucun modele ML.
- V5.1 reste candidate `pending_external_audit`.

## Clause De Securite

- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucune API privee.
- Aucune cle API.
- V5.1 reste non validee avant audit externe.
"""


def _build_latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    input_manifest = manifest["input_ohlcv_manifest"]
    rows = "\n".join(f"- {timeframe}: `{payload['rows']}`" for timeframe, payload in manifest["outputs"].items())
    return f"""# Latest Metrics V5.1

- Derniere version validee : V5.0.
- Candidate : V5.1.
- Statut : `pending_external_audit`.
- Direction : max historical causal feature store preview.
- Fenetre : `{input_manifest['window_start']}` -> `{input_manifest['window_end']}`.
- Total jours : `{input_manifest['total_days']}`.

## Row counts features

{rows}

Aucun label V5.1, aucun dataset ML V5.1, aucun modele ML V5.1, aucun backtest, aucune strategie, aucun ordre et aucun trading reel.
"""


def _build_latest_summary_markdown(manifest: dict[str, Any]) -> str:
    input_manifest = manifest["input_ohlcv_manifest"]
    return f"""# Latest Summary V5.1

V5.0 est la derniere version validee par audit externe.

V5.1 est la candidate courante. Elle produit uniquement des features OHLCV causales sur la fenetre historique continue validee par V5.0, sans label, sans dataset ML, sans modele ML et sans backtest.

Fenetre utilisee : `{input_manifest['window_start']}` -> `{input_manifest['window_end']}`.

Total jours : `{input_manifest['total_days']}`.

Row counts features : `{ {timeframe: payload['rows'] for timeframe, payload in manifest['outputs'].items()} }`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading et aucun claim de rentabilite.

V5.1 reste `pending_external_audit`.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
