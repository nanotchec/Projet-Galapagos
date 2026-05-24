from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.max_history_window_datacard import build_datacard_markdown_v5_3, build_quality_markdown_v5_3
from galapagos.datasets.max_history_window_quality import assess_max_history_dataset_quality
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V5_3,
    DATASET_SCHEMA_VERSION_V5_3,
    DATACARD_MD_PATH_V5_3,
    DOC_PATH_V5_3,
    EXPECTED_LIMITATIONS_V5_3,
    FEATURE_VALUE_COLUMNS,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V5_3,
    REPORT_JSON_PATH_V5_3,
    REPORT_MD_PATH_V5_3,
    SPLIT_COLUMNS_V5_3,
    SPLIT_POLICY_V5_3,
    TIMEFRAMES_V5_3,
    VERSION_V5_3,
    get_dataset_v5_3_path,
    get_split_v5_3_path,
)
from galapagos.features.max_history_window import MANIFEST_PATH_V5_1 as FEATURE_MANIFEST_PATH_V5_1
from galapagos.features.max_history_window_validation import validate_max_history_causal_feature_store_v5_1
from galapagos.labels.max_history_window import MANIFEST_PATH_V5_2 as LABEL_MANIFEST_PATH_V5_2
from galapagos.labels.max_history_window_validation import validate_max_history_label_factory_v5_2


def run_max_history_offline_supervised_dataset_v5_3(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        _validate_inputs(root)

    feature_manifest = load_v5_1_feature_manifest(root)
    label_manifest = load_v5_2_label_manifest(root)
    _validate_input_windows(feature_manifest, label_manifest)
    window_start = feature_manifest["input_ohlcv_manifest"]["window_start"]
    window_end = feature_manifest["input_ohlcv_manifest"]["window_end"]
    total_days = int(feature_manifest["input_ohlcv_manifest"]["total_days"])

    created_at = utc_now_iso()
    dataset_run_id = f"v5_3_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_features: dict[str, dict[str, Any]] = {}
    input_labels: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    splits: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V5_3:
        feature_path = input_feature_path(root, timeframe, feature_manifest)
        label_path = input_label_path(root, timeframe, label_manifest)
        feature_frame = read_parquet(feature_path)
        label_frame = read_parquet(label_path)
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)
        expected_rows = int(feature_manifest["outputs"][timeframe]["rows"])
        if expected_rows != int(label_manifest["outputs"][timeframe]["rows"]):
            raise RuntimeError(f"V5.3 input row count mismatch for {timeframe}")

        dataset = build_max_history_offline_supervised_dataset_v5_3(
            feature_frame,
            label_frame,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=dataset_run_id,
        )
        split_frame = build_split_frame_v5_3(dataset)

        dataset_path = dataset_output_path(root, timeframe, window_start, window_end)
        split_path = split_output_path(root, timeframe, window_start, window_end)
        write_parquet(dataset, dataset_path)
        write_parquet(split_frame, split_path)

        input_features[timeframe] = _input_block(root, feature_path, feature_sha, len(feature_frame))
        input_labels[timeframe] = _input_block(root, label_path, label_sha, len(label_frame))
        outputs[timeframe] = _output_block(root, dataset_path, len(dataset))
        splits[timeframe] = _output_block(root, split_path, len(split_frame))
        quality[timeframe] = assess_max_history_dataset_quality(
            dataset,
            split_frame,
            expected_rows=expected_rows,
            timeframe=timeframe,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
        )
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V5_3,
        "status": status,
        "created_at_utc": created_at,
        "dataset_run_id": dataset_run_id,
        "input_features_manifest": {
            "path": FEATURE_MANIFEST_PATH_V5_1.as_posix(),
            "sha256": sha256_file(root / FEATURE_MANIFEST_PATH_V5_1),
            "window_start": window_start,
            "window_end": window_end,
            "total_days": total_days,
        },
        "input_labels_manifest": {
            "path": LABEL_MANIFEST_PATH_V5_2.as_posix(),
            "sha256": sha256_file(root / LABEL_MANIFEST_PATH_V5_2),
            "window_start": label_manifest["input_ohlcv_manifest"]["window_start"],
            "window_end": label_manifest["input_ohlcv_manifest"]["window_end"],
            "total_days": int(label_manifest["input_ohlcv_manifest"]["total_days"]),
        },
        "input_features": input_features,
        "input_labels": input_labels,
        "outputs": outputs,
        "splits": splits,
        "dataset_schema_version": DATASET_SCHEMA_VERSION_V5_3,
        "dataset_columns": DATASET_COLUMNS_V5_3,
        "split_policy": SPLIT_POLICY_V5_3,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V5_3,
    }
    report = _build_report(manifest)
    _write_json(root / MANIFEST_PATH_V5_3, manifest)
    _write_json(root / REPORT_JSON_PATH_V5_3, report)
    quality_markdown = build_quality_markdown_v5_3(manifest)
    datacard = build_datacard_markdown_v5_3(manifest)
    _write_text(root / REPORT_MD_PATH_V5_3, quality_markdown)
    _write_text(root / DATACARD_MD_PATH_V5_3, datacard)
    _write_text(root / DOC_PATH_V5_3, quality_markdown)
    _update_project_state(root, manifest)
    return manifest


def build_max_history_offline_supervised_dataset_v5_3(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    feature_sha256: str,
    label_sha256: str,
    dataset_run_id: str,
) -> pd.DataFrame:
    _require_columns(features, [*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS], "features")
    _require_columns(labels, [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS], "labels")

    feature_block = features[[*JOIN_KEYS, "feature_available_ts", *FEATURE_VALUE_COLUMNS]].copy()
    label_block = labels[[*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]].copy()
    merged = feature_block.merge(label_block, on=JOIN_KEYS, how="inner", validate="one_to_one")
    merged = merged.sort_values("event_ts").reset_index(drop=True)
    merged["dataset_run_id"] = dataset_run_id
    merged["dataset_schema_version"] = DATASET_SCHEMA_VERSION_V5_3
    merged["source_features_sha256"] = feature_sha256
    merged["source_labels_sha256"] = label_sha256
    merged = assign_temporal_splits_v5_3(merged)
    merged["dataset_error_count"] = 0
    null_columns = [column for column in DATASET_COLUMNS_V5_3 if column != "dataset_null_count"]
    merged["dataset_null_count"] = merged[null_columns].isna().sum(axis=1).astype(int)
    return merged[DATASET_COLUMNS_V5_3].copy()


def assign_temporal_splits_v5_3(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("event_ts").reset_index(drop=True).copy()
    rows = len(ordered)
    train_end = int(rows * SPLIT_POLICY_V5_3["train_ratio"])
    validation_end = train_end + int(rows * SPLIT_POLICY_V5_3["validation_ratio"])
    ordered["split"] = "test"
    ordered.loc[: train_end - 1, "split"] = "train"
    ordered.loc[train_end : validation_end - 1, "split"] = "validation"
    ordered["split_order"] = range(rows)
    ordered["purge_embargo_group"] = SPLIT_POLICY_V5_3["purge_embargo"]
    return ordered


def build_split_frame_v5_3(dataset: pd.DataFrame) -> pd.DataFrame:
    _require_columns(dataset, [column for column in SPLIT_COLUMNS_V5_3 if column != "walk_forward_group"], "dataset")
    split_frame = dataset[[column for column in SPLIT_COLUMNS_V5_3 if column != "walk_forward_group"]].copy()
    event_ts = pd.to_datetime(split_frame["event_ts"], utc=True)
    quarters = ((event_ts.dt.month - 1) // 3 + 1).astype(int)
    split_frame["walk_forward_group"] = "wf_" + event_ts.dt.year.astype(str) + "_Q" + quarters.astype(str)
    return split_frame[SPLIT_COLUMNS_V5_3].copy()


def load_v5_1_feature_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / FEATURE_MANIFEST_PATH_V5_1).read_text(encoding="utf-8"))


def load_v5_2_label_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / LABEL_MANIFEST_PATH_V5_2).read_text(encoding="utf-8"))


def input_feature_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v5_1_feature_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def input_label_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v5_2_label_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def dataset_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        manifest = load_v5_1_feature_manifest(root)
        window_start = manifest["input_ohlcv_manifest"]["window_start"]
        window_end = manifest["input_ohlcv_manifest"]["window_end"]
    return get_dataset_v5_3_path(root.resolve(), timeframe, window_start, window_end)


def split_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        manifest = load_v5_1_feature_manifest(root)
        window_start = manifest["input_ohlcv_manifest"]["window_start"]
        window_end = manifest["input_ohlcv_manifest"]["window_end"]
    return get_split_v5_3_path(root.resolve(), timeframe, window_start, window_end)


def _validate_inputs(root: Path) -> None:
    validators = [
        ("V5.1 max-history features", validate_max_history_causal_feature_store_v5_1),
        ("V5.2 max-history labels", validate_max_history_label_factory_v5_2),
    ]
    for label, validator in validators:
        result = validator(root)
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed before V5.3: {result['errors']}")


def _validate_input_windows(feature_manifest: dict[str, Any], label_manifest: dict[str, Any]) -> None:
    feature_window = feature_manifest["input_ohlcv_manifest"]
    label_window = label_manifest["input_ohlcv_manifest"]
    for key in ["window_start", "window_end", "total_days"]:
        if feature_window[key] != label_window[key]:
            raise RuntimeError(f"V5.3 input window mismatch for {key}: features={feature_window[key]}, labels={label_window[key]}")
    for timeframe in TIMEFRAMES_V5_3:
        if int(feature_manifest["outputs"][timeframe]["rows"]) != int(label_manifest["outputs"][timeframe]["rows"]):
            raise RuntimeError(f"V5.3 input rows mismatch for {timeframe}")


def _input_block(root: Path, path: Path, sha256: str, rows: int) -> dict[str, Any]:
    return {"path": str(path.relative_to(root)), "sha256": sha256, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(rows),
        "format": "parquet",
    }


def _build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "dataset_run_id": manifest["dataset_run_id"],
        "input_features_manifest": manifest["input_features_manifest"],
        "input_labels_manifest": manifest["input_labels_manifest"],
        "input_features": manifest["input_features"],
        "input_labels": manifest["input_labels"],
        "outputs": manifest["outputs"],
        "splits": manifest["splits"],
        "dataset_schema_version": manifest["dataset_schema_version"],
        "dataset_columns": manifest["dataset_columns"],
        "split_policy": manifest["split_policy"],
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
        "dataset_enabled": True,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
    }


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    split_counts = {timeframe: manifest["quality"][timeframe]["split_counts"] for timeframe in TIMEFRAMES_V5_3}
    feature_window = manifest["input_features_manifest"]
    state.update(
        {
            "last_validated_version": "V5.2",
            "candidate_version": "V5.3",
            "candidate_status": "pending_external_audit",
            "direction": "max historical offline supervised dataset assembly preview",
            "v5_3_candidate": True,
            "max_history_offline_supervised_dataset_v5_3_created": True,
            "max_history_dataset_window_start_v5_3": feature_window["window_start"],
            "max_history_dataset_window_end_v5_3": feature_window["window_end"],
            "max_history_dataset_days_v5_3": feature_window["total_days"],
            "max_history_dataset_rows_v5_3": rows,
            "max_history_dataset_split_counts_v5_3": split_counts,
            "ml_v5_3_created": False,
            "model_v5_3_created": False,
            "backtest_v5_3_created": False,
            "strategy_v5_3_created": False,
            "signal_v5_3_created": False,
            "orders_v5_3_created": False,
            "paper_live_v5_3_created": False,
            "trading_v5_3_created": False,
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
    split_counts = {timeframe: manifest["quality"][timeframe]["split_counts"] for timeframe in TIMEFRAMES_V5_3}
    feature_window = manifest["input_features_manifest"]
    return {
        "last_validated_version": "V5.2",
        "candidate_version": "V5.3",
        "candidate_status": "pending_external_audit",
        "direction": state["direction"],
        "max_history_dataset_window_start_v5_3": feature_window["window_start"],
        "max_history_dataset_window_end_v5_3": feature_window["window_end"],
        "max_history_dataset_days_v5_3": feature_window["total_days"],
        "max_history_dataset_rows_v5_3": rows,
        "max_history_dataset_split_counts_v5_3": split_counts,
        "dataset_schema_version_v5_3": DATASET_SCHEMA_VERSION_V5_3,
        "dataset_columns_count_v5_3": len(DATASET_COLUMNS_V5_3),
        "walk_forward_grouping_v5_3": SPLIT_POLICY_V5_3["walk_forward_grouping"],
        "ml_v5_3_created": False,
        "model_v5_3_created": False,
        "backtest_v5_3_created": False,
        "strategy_v5_3_created": False,
        "signal_v5_3_created": False,
        "orders_v5_3_created": False,
        "paper_live_v5_3_created": False,
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
    split_counts = {timeframe: manifest["quality"][timeframe]["split_counts"] for timeframe in TIMEFRAMES_V5_3}
    feature_window = manifest["input_features_manifest"]
    return f"""# Etat du Projet : V5.2 validee + candidat V5.3

- **Derniere version validee** : V5.2.
- **Version candidate** : V5.3.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : max historical offline supervised dataset assembly preview.

## Candidat V5.3

- Fenetre V5.0 utilisee : `{feature_window['window_start']}` -> `{feature_window['window_end']}`.
- Nombre de jours : `{feature_window['total_days']}`.
- Row counts datasets : `{rows}`.
- Split counts : `{split_counts}`.
- Schema : `DATASET_COLUMNS_V5_3`.
- Groupes walk-forward : `calendar_quarter`.
- V5.3 ne cree aucun ML et aucun modele.
- V5.3 reste candidate `pending_external_audit`.

## Clause De Securite

- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucune API privee.
- Aucune cle API.
- V5.3 reste non validee avant audit externe.
"""


def _build_latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    feature_window = manifest["input_features_manifest"]
    rows = "\n".join(f"- {timeframe}: `{payload['rows']}`" for timeframe, payload in manifest["outputs"].items())
    return f"""# Latest Metrics V5.3

- Derniere version validee : V5.2.
- Candidate : V5.3.
- Statut : `pending_external_audit`.
- Direction : max historical offline supervised dataset assembly preview.
- Fenetre : `{feature_window['window_start']}` -> `{feature_window['window_end']}`.
- Total jours : `{feature_window['total_days']}`.
- Groupes walk-forward : `calendar_quarter`.

## Row counts datasets

{rows}

Aucun ML V5.3, aucun modele V5.3, aucun backtest, aucune strategie, aucun ordre et aucun trading reel.
"""


def _build_latest_summary_markdown(manifest: dict[str, Any]) -> str:
    feature_window = manifest["input_features_manifest"]
    rows = {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()}
    return f"""# Latest Summary V5.3

V5.2 est la derniere version validee par audit externe.

V5.3 est la candidate courante. Elle assemble uniquement un dataset supervise offline sur la fenetre historique continue V5.0 a partir des features V5.1 et labels V5.2, sans ML, sans modele et sans backtest.

Fenetre utilisee : `{feature_window['window_start']}` -> `{feature_window['window_end']}`.

Total jours : `{feature_window['total_days']}`.

Row counts datasets : `{rows}`.

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading et aucun claim de rentabilite.

V5.3 reste `pending_external_audit`.
"""


def _require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required {label} columns: {missing}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
