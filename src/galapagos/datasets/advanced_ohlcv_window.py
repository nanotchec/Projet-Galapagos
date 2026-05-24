from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.advanced_ohlcv_window_datacard import build_datacard_markdown_v6_1, build_quality_markdown_v6_1
from galapagos.datasets.advanced_ohlcv_window_quality import assess_advanced_ohlcv_dataset_quality
from galapagos.datasets.schemas import (
    ADVANCED_DATASET_FEATURE_COLUMNS_V6_1,
    DATASET_COLUMNS_V6_1,
    DATASET_SCHEMA_VERSION_V6_1,
    DATACARD_MD_PATH_V6_1,
    DOC_PATH_V6_1,
    EXPECTED_LIMITATIONS_V6_1,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V6_1,
    REPORT_JSON_PATH_V6_1,
    REPORT_MD_PATH_V6_1,
    SPLIT_COLUMNS_V6_1,
    SPLIT_POLICY_V6_1,
    TIMEFRAMES_V6_1,
    VERSION_V6_1,
    get_dataset_v6_1_path,
    get_split_v6_1_path,
)
from galapagos.features.advanced_ohlcv import MANIFEST_PATH_V6_0 as FEATURE_MANIFEST_PATH_V6_0
from galapagos.features.advanced_ohlcv_validation import validate_advanced_ohlcv_feature_store_v6_0
from galapagos.features.advanced_ohlcv_schemas import ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0
from galapagos.labels.max_history_window import MANIFEST_PATH_V5_2 as LABEL_MANIFEST_PATH_V5_2
from galapagos.labels.max_history_window_validation import validate_max_history_label_factory_v5_2


def run_advanced_ohlcv_offline_supervised_dataset_v6_1(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        _validate_inputs(root)

    feature_manifest = load_v6_0_feature_manifest(root)
    label_manifest = load_v5_2_label_manifest(root)
    _validate_input_windows(feature_manifest, label_manifest)
    window_start = feature_manifest["input_ohlcv_manifest"]["window_start"]
    window_end = feature_manifest["input_ohlcv_manifest"]["window_end"]
    total_days = int(feature_manifest["input_ohlcv_manifest"]["total_days"])

    created_at = utc_now_iso()
    dataset_run_id = f"v6_1_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_features: dict[str, dict[str, Any]] = {}
    input_labels: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    splits: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V6_1:
        feature_path = input_feature_path(root, timeframe, feature_manifest)
        label_path = input_label_path(root, timeframe, label_manifest)
        feature_frame = read_parquet(feature_path)
        label_frame = read_parquet(label_path)
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)
        expected_rows = int(feature_manifest["outputs"][timeframe]["rows"])
        if expected_rows != int(label_manifest["outputs"][timeframe]["rows"]):
            raise RuntimeError(f"V6.1 input row count mismatch for {timeframe}")

        dataset = build_advanced_ohlcv_offline_supervised_dataset_v6_1(
            feature_frame,
            label_frame,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=dataset_run_id,
        )
        split_frame = build_split_frame_v6_1(dataset)
        dataset_path = dataset_output_path(root, timeframe, window_start, window_end)
        split_path = split_output_path(root, timeframe, window_start, window_end)
        write_parquet(dataset, dataset_path)
        write_parquet(split_frame, split_path)

        input_features[timeframe] = _input_block(root, feature_path, feature_sha, len(feature_frame))
        input_labels[timeframe] = _input_block(root, label_path, label_sha, len(label_frame))
        outputs[timeframe] = _output_block(root, dataset_path, len(dataset))
        splits[timeframe] = _output_block(root, split_path, len(split_frame))
        quality[timeframe] = assess_advanced_ohlcv_dataset_quality(
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
        "version": VERSION_V6_1,
        "status": status,
        "created_at_utc": created_at,
        "dataset_run_id": dataset_run_id,
        "input_features_manifest": {
            "path": FEATURE_MANIFEST_PATH_V6_0.as_posix(),
            "sha256": sha256_file(root / FEATURE_MANIFEST_PATH_V6_0),
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
        "dataset_schema_version": DATASET_SCHEMA_VERSION_V6_1,
        "dataset_columns": DATASET_COLUMNS_V6_1,
        "advanced_feature_columns_count": len(ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0),
        "split_policy": SPLIT_POLICY_V6_1,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V6_1,
    }
    report = build_report_v6_1(manifest)
    _write_json(root / MANIFEST_PATH_V6_1, manifest)
    _write_json(root / REPORT_JSON_PATH_V6_1, report)
    quality_markdown = build_quality_markdown_v6_1(manifest)
    datacard = build_datacard_markdown_v6_1(manifest)
    _write_text(root / REPORT_MD_PATH_V6_1, quality_markdown)
    _write_text(root / DATACARD_MD_PATH_V6_1, datacard)
    _write_text(root / DOC_PATH_V6_1, quality_markdown)
    _update_project_state(root, manifest)
    return manifest


def build_advanced_ohlcv_offline_supervised_dataset_v6_1(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    feature_sha256: str,
    label_sha256: str,
    dataset_run_id: str,
) -> pd.DataFrame:
    _require_columns(features, [*JOIN_KEYS, "feature_available_ts", *ADVANCED_DATASET_FEATURE_COLUMNS_V6_1], "advanced features")
    _require_columns(labels, [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS], "labels")

    feature_block = features[[*JOIN_KEYS, "feature_available_ts", *ADVANCED_DATASET_FEATURE_COLUMNS_V6_1]].sort_values("event_ts").reset_index(drop=True)
    label_block = labels[[*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]].sort_values("event_ts").reset_index(drop=True)
    if len(feature_block) != len(label_block):
        raise RuntimeError(f"V6.1 source row count mismatch: features={len(feature_block)}, labels={len(label_block)}")
    try:
        pd.testing.assert_frame_equal(
            feature_block[JOIN_KEYS],
            label_block[JOIN_KEYS],
            check_dtype=False,
        )
    except AssertionError as exc:
        raise RuntimeError(f"V6.1 join key mismatch: {str(exc).splitlines()[0]}") from exc

    merged = pd.concat(
        [
            feature_block[[*JOIN_KEYS, "feature_available_ts", *ADVANCED_DATASET_FEATURE_COLUMNS_V6_1]],
            label_block[["label_available_ts", *LABEL_VALUE_COLUMNS]],
        ],
        axis=1,
    )
    merged["dataset_run_id"] = dataset_run_id
    merged["dataset_schema_version"] = DATASET_SCHEMA_VERSION_V6_1
    merged["source_features_sha256"] = feature_sha256
    merged["source_labels_sha256"] = label_sha256
    merged = assign_temporal_splits_v6_1(merged)
    merged["dataset_error_count"] = 0
    null_columns = [column for column in DATASET_COLUMNS_V6_1 if column != "dataset_null_count"]
    merged["dataset_null_count"] = merged[null_columns].isna().sum(axis=1).astype("int16")
    return merged[DATASET_COLUMNS_V6_1].copy()


def assign_temporal_splits_v6_1(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("event_ts").reset_index(drop=True).copy()
    rows = len(ordered)
    train_end = int(rows * SPLIT_POLICY_V6_1["train_ratio"])
    validation_end = train_end + int(rows * SPLIT_POLICY_V6_1["validation_ratio"])
    ordered["split"] = "test"
    ordered.loc[: train_end - 1, "split"] = "train"
    ordered.loc[train_end : validation_end - 1, "split"] = "validation"
    ordered["split_order"] = range(rows)
    ordered["purge_embargo_group"] = SPLIT_POLICY_V6_1["purge_embargo"]
    event_ts = pd.to_datetime(ordered["event_ts"], utc=True)
    quarters = ((event_ts.dt.month - 1) // 3 + 1).astype(int)
    ordered["walk_forward_group"] = "wf_" + event_ts.dt.year.astype(str) + "_Q" + quarters.astype(str)
    return ordered


def build_split_frame_v6_1(dataset: pd.DataFrame) -> pd.DataFrame:
    _require_columns(dataset, SPLIT_COLUMNS_V6_1, "dataset")
    return dataset[SPLIT_COLUMNS_V6_1].copy()


def load_v6_0_feature_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / FEATURE_MANIFEST_PATH_V6_0).read_text(encoding="utf-8"))


def load_v5_2_label_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / LABEL_MANIFEST_PATH_V5_2).read_text(encoding="utf-8"))


def input_feature_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v6_0_feature_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def input_label_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v5_2_label_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def dataset_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        manifest = load_v6_0_feature_manifest(root)
        window_start = manifest["input_ohlcv_manifest"]["window_start"]
        window_end = manifest["input_ohlcv_manifest"]["window_end"]
    return get_dataset_v6_1_path(root.resolve(), timeframe, window_start, window_end)


def split_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    if window_start is None or window_end is None:
        manifest = load_v6_0_feature_manifest(root)
        window_start = manifest["input_ohlcv_manifest"]["window_start"]
        window_end = manifest["input_ohlcv_manifest"]["window_end"]
    return get_split_v6_1_path(root.resolve(), timeframe, window_start, window_end)


def build_report_v6_1(manifest: dict[str, Any]) -> dict[str, Any]:
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
        "advanced_feature_columns_count": manifest["advanced_feature_columns_count"],
        "split_policy": manifest["split_policy"],
        "quality": manifest["quality"],
        "safety": manifest["safety"],
        "limitations": manifest["limitations"],
    }


def _validate_inputs(root: Path) -> None:
    validators = [
        ("V6.0 advanced OHLCV features", validate_advanced_ohlcv_feature_store_v6_0),
        ("V5.2 max-history labels", validate_max_history_label_factory_v5_2),
    ]
    for label, validator in validators:
        result = validator(root)
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed before V6.1: {result['errors']}")


def _validate_input_windows(feature_manifest: dict[str, Any], label_manifest: dict[str, Any]) -> None:
    feature_window = feature_manifest["input_ohlcv_manifest"]
    label_window = label_manifest["input_ohlcv_manifest"]
    for key in ["window_start", "window_end", "total_days"]:
        if feature_window[key] != label_window[key]:
            raise RuntimeError(f"V6.1 input window mismatch for {key}: features={feature_window[key]}, labels={label_window[key]}")
    for timeframe in TIMEFRAMES_V6_1:
        if int(feature_manifest["outputs"][timeframe]["rows"]) != int(label_manifest["outputs"][timeframe]["rows"]):
            raise RuntimeError(f"V6.1 input rows mismatch for {timeframe}")


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


def _require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise RuntimeError(f"V6.1 {label} missing columns: {missing}")


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V6.0",
            "candidate_version": VERSION_V6_1,
            "candidate_status": "pending_external_audit",
            "direction": "max historical offline supervised dataset with advanced OHLCV features",
            "v6_1_pending_external_audit": True,
            "v6_1_no_ml": True,
            "v6_1_no_model": True,
            "v6_1_no_backtest": True,
            "v6_1_no_strategy": True,
            "v6_1_no_paper_live": True,
            "v6_1_no_orders": True,
            "v6_1_no_real_trading": True,
        }
    )
    _write_json(state_path, state)
    _write_text(root / "reports/PROJECT_STATE.md", _render_project_state_markdown(manifest))
    _write_json(root / "reports/current/latest_metrics.json", build_report_v6_1(manifest))
    _write_text(root / "reports/current/latest_metrics.md", _render_latest_metrics_markdown(manifest))
    _write_text(root / "reports/current/latest_summary.md", _render_latest_summary_markdown(manifest))


def _render_project_state_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Etat projet Galapagos

- Derniere version validee : `V6.0`
- Candidate : `V6.1`
- Statut candidate : `pending_external_audit`
- Direction : max historical offline supervised dataset with advanced OHLCV features
- Fenetre : `{manifest['input_features_manifest']['window_start']}` -> `{manifest['input_features_manifest']['window_end']}`
- Aucun ML V6.1
- Aucun modele V6.1
- Aucun backtest
- Aucune strategie
- Aucun paper live
- Aucun ordre
- Aucun trading reel
"""


def _render_latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    outputs = "\n".join(
        f"- `{timeframe}` : dataset `{payload['rows']}` lignes, checksum `{payload['sha256']}`"
        for timeframe, payload in manifest["outputs"].items()
    )
    splits = "\n".join(
        f"- `{timeframe}` : splits `{payload['rows']}` lignes, checksum `{payload['sha256']}`"
        for timeframe, payload in manifest["splits"].items()
    )
    return f"""# Latest metrics V6.1

- Version candidate : `V6.1`
- Statut : `pending_external_audit`
- Type : dataset supervise offline advanced OHLCV
- Nombre de colonnes dataset : `{len(DATASET_COLUMNS_V6_1)}`
- Nombre de colonnes advanced features : `{manifest['advanced_feature_columns_count']}`

## Datasets

{outputs}

## Splits

{splits}

## Securite

Aucun ML, aucun modele, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun trading reel.
"""


def _render_latest_summary_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Synthese courante

La derniere version validee reste `V6.0`. La candidate `V6.1` est en statut `pending_external_audit`.

V6.1 assemble uniquement un dataset supervise offline avec les advanced OHLCV features V6.0 et les labels V5.2 sur la fenetre max historical validee (`{manifest['input_features_manifest']['window_start']}` -> `{manifest['input_features_manifest']['window_end']}`, `{manifest['input_features_manifest']['total_days']}` jours).

V6.1 ne produit aucun ML, aucun modele, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live et aucun trading reel.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
