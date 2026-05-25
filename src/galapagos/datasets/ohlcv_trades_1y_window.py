from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.ohlcv_trades_1y_window_datacard import build_datacard_markdown_v8_4, build_quality_markdown_v8_4
from galapagos.datasets.ohlcv_trades_1y_window_quality import assess_ohlcv_trades_dataset_quality_v8_4
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V8_4,
    DATASET_SCHEMA_VERSION_V8_4,
    DATACARD_MD_PATH_V8_4,
    DOC_PATH_V8_4,
    EXPECTED_LIMITATIONS_V8_4,
    EXPECTED_ROWS_V8_4,
    JOIN_KEYS,
    LABEL_VALUE_COLUMNS,
    MANIFEST_PATH_V8_4,
    OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4,
    REPORT_JSON_PATH_V8_4,
    REPORT_MD_PATH_V8_4,
    SPLIT_COLUMNS_V8_4,
    SPLIT_POLICY_V8_4,
    TIMEFRAMES_V8_4,
    VERSION_V8_4,
    get_dataset_v8_4_path,
    get_split_v8_4_path,
)
from galapagos.features.ohlcv_trades_1y import (
    MANIFEST_PATH_V8_3 as FEATURE_MANIFEST_PATH_V8_3,
    WINDOW_END_V8_3,
    WINDOW_START_V8_3,
    output_path as feature_output_path_v8_3,
)
from galapagos.features.ohlcv_trades_1y_validation import validate_ohlcv_trades_1y_feature_store_v8_3
from galapagos.labels.max_history_window import MANIFEST_PATH_V5_2 as LABEL_MANIFEST_PATH_V5_2
from galapagos.labels.max_history_window_validation import validate_max_history_label_factory_v5_2


WINDOW_START_V8_4 = WINDOW_START_V8_3
WINDOW_END_V8_4 = WINDOW_END_V8_3
TOTAL_DAYS_V8_4 = 366


def run_ohlcv_trades_1y_offline_supervised_dataset_v8_4(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    project_root = root.resolve()
    if validate_inputs:
        _validate_inputs(project_root)

    feature_manifest = load_v8_3_feature_manifest(project_root)
    label_manifest = load_v5_2_label_manifest(project_root)
    _validate_input_windows(feature_manifest, label_manifest)

    created_at = utc_now_iso()
    dataset_run_id = f"v8_4_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_features: dict[str, dict[str, Any]] = {}
    input_labels_filtered: dict[str, dict[str, int]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    splits: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V8_4:
        feature_path = input_feature_path(project_root, timeframe, feature_manifest)
        label_path = input_label_path(project_root, timeframe, label_manifest)
        feature_frame = read_parquet(feature_path)
        label_frame = filter_labels_to_v8_4_window(read_parquet(label_path))
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)
        expected_rows = EXPECTED_ROWS_V8_4[timeframe]
        if len(feature_frame) != expected_rows or len(label_frame) != expected_rows:
            raise RuntimeError(
                f"V8.4 input row count mismatch for {timeframe}: features={len(feature_frame)}, filtered_labels={len(label_frame)}, expected={expected_rows}"
            )

        dataset = build_ohlcv_trades_1y_offline_supervised_dataset_v8_4(
            feature_frame,
            label_frame,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=dataset_run_id,
        )
        split_frame = build_split_frame_v8_4(dataset)
        dataset_path = dataset_output_path(project_root, timeframe, WINDOW_START_V8_4, WINDOW_END_V8_4)
        split_path = split_output_path(project_root, timeframe, WINDOW_START_V8_4, WINDOW_END_V8_4)
        write_parquet(dataset, dataset_path)
        write_parquet(split_frame, split_path)

        input_features[timeframe] = _input_block(project_root, feature_path, feature_sha, len(feature_frame))
        input_labels_filtered[timeframe] = {"rows": int(len(label_frame))}
        outputs[timeframe] = _output_block(project_root, dataset_path, len(dataset))
        splits[timeframe] = _output_block(project_root, split_path, len(split_frame))
        quality[timeframe] = assess_ohlcv_trades_dataset_quality_v8_4(
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
        "version": VERSION_V8_4,
        "status": status,
        "created_at_utc": created_at,
        "dataset_run_id": dataset_run_id,
        "input_features_manifest": {
            "path": FEATURE_MANIFEST_PATH_V8_3.as_posix(),
            "sha256": sha256_file(project_root / FEATURE_MANIFEST_PATH_V8_3),
            "window_start": feature_manifest["window"]["window_start"],
            "window_end": feature_manifest["window"]["window_end"],
            "total_days": int(feature_manifest["window"]["total_days"]),
        },
        "input_labels_manifest": {
            "path": LABEL_MANIFEST_PATH_V5_2.as_posix(),
            "sha256": sha256_file(project_root / LABEL_MANIFEST_PATH_V5_2),
            "source_window_start": label_manifest["input_ohlcv_manifest"]["window_start"],
            "source_window_end": label_manifest["input_ohlcv_manifest"]["window_end"],
            "dataset_window_start": WINDOW_START_V8_4,
            "dataset_window_end": WINDOW_END_V8_4,
        },
        "input_features": input_features,
        "input_labels_filtered": input_labels_filtered,
        "outputs": outputs,
        "splits": splits,
        "dataset_schema_version": DATASET_SCHEMA_VERSION_V8_4,
        "dataset_columns": DATASET_COLUMNS_V8_4,
        "feature_columns_count": len(OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4),
        "split_policy": SPLIT_POLICY_V8_4,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V8_4,
    }
    report = build_report_v8_4(manifest)
    _write_json(project_root / MANIFEST_PATH_V8_4, manifest)
    _write_json(project_root / REPORT_JSON_PATH_V8_4, report)
    quality_markdown = build_quality_markdown_v8_4(manifest)
    datacard = build_datacard_markdown_v8_4(manifest)
    _write_text(project_root / REPORT_MD_PATH_V8_4, quality_markdown)
    _write_text(project_root / DATACARD_MD_PATH_V8_4, datacard)
    _write_text(project_root / DOC_PATH_V8_4, quality_markdown)
    update_project_state_v8_4(project_root, manifest)
    return manifest


def build_ohlcv_trades_1y_offline_supervised_dataset_v8_4(
    features: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    feature_sha256: str,
    label_sha256: str,
    dataset_run_id: str,
) -> pd.DataFrame:
    _require_columns(features, [*JOIN_KEYS, "feature_available_ts", *OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4], "OHLCV+trades features")
    _require_columns(labels, [*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS], "labels")
    feature_block = features[[*JOIN_KEYS, "feature_available_ts", *OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4]].sort_values("event_ts").reset_index(drop=True)
    label_block = labels[[*JOIN_KEYS, "label_available_ts", *LABEL_VALUE_COLUMNS]].sort_values("event_ts").reset_index(drop=True)
    if len(feature_block) != len(label_block):
        raise RuntimeError(f"V8.4 source row count mismatch: features={len(feature_block)}, labels={len(label_block)}")
    try:
        pd.testing.assert_frame_equal(feature_block[JOIN_KEYS], label_block[JOIN_KEYS], check_dtype=False)
    except AssertionError as exc:
        raise RuntimeError(f"V8.4 join key mismatch: {str(exc).splitlines()[0]}") from exc

    merged = pd.concat(
        [
            feature_block[[*JOIN_KEYS, "feature_available_ts", *OHLCV_TRADES_DATASET_FEATURE_COLUMNS_V8_4]],
            label_block[["label_available_ts", *LABEL_VALUE_COLUMNS]],
        ],
        axis=1,
    )
    merged["dataset_run_id"] = dataset_run_id
    merged["dataset_schema_version"] = DATASET_SCHEMA_VERSION_V8_4
    merged["source_features_sha256"] = feature_sha256
    merged["source_labels_sha256"] = label_sha256
    merged = assign_temporal_splits_v8_4(merged)
    merged["dataset_error_count"] = 0
    null_columns = [column for column in DATASET_COLUMNS_V8_4 if column != "dataset_null_count"]
    merged["dataset_null_count"] = merged[null_columns].isna().sum(axis=1).astype("int16")
    return merged[DATASET_COLUMNS_V8_4].copy()


def assign_temporal_splits_v8_4(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("event_ts").reset_index(drop=True).copy()
    rows = len(ordered)
    train_end = int(rows * SPLIT_POLICY_V8_4["train_ratio"])
    validation_rows = (rows - train_end) // 2
    validation_end = train_end + validation_rows
    ordered["split"] = "test"
    ordered.loc[: train_end - 1, "split"] = "train"
    ordered.loc[train_end : validation_end - 1, "split"] = "validation"
    ordered["split_order"] = range(rows)
    ordered["purge_embargo_group"] = SPLIT_POLICY_V8_4["purge_embargo"]
    event_ts = pd.to_datetime(ordered["event_ts"], utc=True)
    month_labels = event_ts.dt.strftime("wf_%Y_%m")
    ordered["walk_forward_group"] = month_labels.mask(month_labels == "wf_2023_03", "wf_2023_03_partial").mask(
        month_labels == "wf_2024_03",
        "wf_2024_03_partial",
    )
    return ordered


def build_split_frame_v8_4(dataset: pd.DataFrame) -> pd.DataFrame:
    _require_columns(dataset, SPLIT_COLUMNS_V8_4, "dataset")
    return dataset[SPLIT_COLUMNS_V8_4].copy()


def filter_labels_to_v8_4_window(labels: pd.DataFrame) -> pd.DataFrame:
    event_ts = pd.to_datetime(labels["event_ts"], utc=True)
    start = pd.Timestamp(f"{WINDOW_START_V8_4}T00:00:00Z")
    end_exclusive = pd.Timestamp("2024-03-25T00:00:00Z")
    return labels.loc[(event_ts >= start) & (event_ts < end_exclusive)].sort_values("event_ts").reset_index(drop=True)


def load_v8_3_feature_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / FEATURE_MANIFEST_PATH_V8_3).read_text(encoding="utf-8"))


def load_v5_2_label_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / LABEL_MANIFEST_PATH_V5_2).read_text(encoding="utf-8"))


def input_feature_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v8_3_feature_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def input_label_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v5_2_label_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def dataset_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    return get_dataset_v8_4_path(root.resolve(), timeframe, window_start or WINDOW_START_V8_4, window_end or WINDOW_END_V8_4)


def split_output_path(root: Path, timeframe: str, window_start: str | None = None, window_end: str | None = None) -> Path:
    return get_split_v8_4_path(root.resolve(), timeframe, window_start or WINDOW_START_V8_4, window_end or WINDOW_END_V8_4)


def build_report_v8_4(manifest: dict[str, Any]) -> dict[str, Any]:
    return dict(manifest)


def update_project_state_v8_4(root: Path, manifest: dict[str, Any]) -> None:
    project_state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(project_state_path) if project_state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V8.3",
            "candidate_version": "V8.4",
            "candidate_status": "pending_external_audit",
            "direction": "OHLCV + public trades 1-year offline supervised dataset preview",
            "ohlcv_trades_dataset_v8_4_created": True,
            "ml_v8_4_created": False,
            "model_v8_4_created": False,
            "backtest_v8_4_created": False,
            "strategy_v8_4_created": False,
            "orders_v8_4_created": False,
            "window_start_v8_4": manifest["input_features_manifest"]["window_start"],
            "window_end_v8_4": manifest["input_features_manifest"]["window_end"],
            "total_days_v8_4": manifest["input_features_manifest"]["total_days"],
            "feature_columns_v8_4_count": manifest["feature_columns_count"],
            "output_rows_v8_4": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()},
            "backtest_enabled": False,
            "strategy_enabled": False,
            "paper_live_enabled": False,
            "orders_enabled": False,
            "trading_enabled": False,
            "execution_enabled": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "authentication_used": False,
            "external_validation_required": True,
        }
    )
    _write_json(project_state_path, state)
    _write_current_reports(root, manifest)


def _validate_inputs(root: Path) -> None:
    feature_validation = validate_ohlcv_trades_1y_feature_store_v8_3(root)
    if not feature_validation["passed"]:
        raise RuntimeError(f"V8.3 validation failed before V8.4: {feature_validation['errors']}")
    label_validation = validate_max_history_label_factory_v5_2(root)
    if not label_validation["passed"]:
        raise RuntimeError(f"V5.2 validation failed before V8.4: {label_validation['errors']}")


def _validate_input_windows(feature_manifest: dict[str, Any], label_manifest: dict[str, Any]) -> None:
    if feature_manifest["window"]["window_start"] != WINDOW_START_V8_4 or feature_manifest["window"]["window_end"] != WINDOW_END_V8_4:
        raise ValueError("V8.4 requires the exact V8.3 feature window.")
    if int(feature_manifest["window"]["total_days"]) != TOTAL_DAYS_V8_4:
        raise ValueError("V8.4 requires a 1-year V8.3 feature window.")
    label_window_start = label_manifest["input_ohlcv_manifest"]["window_start"]
    label_window_end = label_manifest["input_ohlcv_manifest"]["window_end"]
    if WINDOW_START_V8_4 < label_window_start or WINDOW_END_V8_4 > label_window_end:
        raise ValueError("V8.4 labels V5.2 must cover the full V8.3 window.")


def _input_block(root: Path, path: Path, sha256: str, rows: int) -> dict[str, Any]:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha256, "rows": int(rows)}


def _output_block(root: Path, path: Path, rows: int) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
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


def _write_current_reports(root: Path, manifest: dict[str, Any]) -> None:
    latest_metrics = {
        "last_validated_version": "V8.3",
        "candidate_version": "V8.4",
        "candidate_status": "pending_external_audit",
        "direction": "OHLCV + public trades 1-year offline supervised dataset preview",
        "window_start": manifest["input_features_manifest"]["window_start"],
        "window_end": manifest["input_features_manifest"]["window_end"],
        "total_days": manifest["input_features_manifest"]["total_days"],
        "feature_columns_count": manifest["feature_columns_count"],
        "output_rows": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()},
        "ml_v8_4_created": False,
        "model_v8_4_created": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "execution_enabled": False,
        "external_validation_required": True,
    }
    _write_json(root / "reports/current/latest_metrics.json", latest_metrics)
    _write_text(
        root / "reports/current/latest_metrics.md",
        "\n".join(
            [
                "# Latest Metrics V8.4",
                "",
                "- Derniere version validee : V8.3.",
                "- Candidate : V8.4.",
                "- Direction : OHLCV + public trades 1-year offline supervised dataset preview.",
                f"- Fenetre : `{manifest['input_features_manifest']['window_start']}` -> `{manifest['input_features_manifest']['window_end']}`.",
                f"- Total jours : `{manifest['input_features_manifest']['total_days']}`.",
                f"- Colonnes features : `{manifest['feature_columns_count']}`.",
                f"- Rows 1m/5m/15m/1h : `{manifest['outputs']['1m']['rows']}` / `{manifest['outputs']['5m']['rows']}` / `{manifest['outputs']['15m']['rows']}` / `{manifest['outputs']['1h']['rows']}`.",
                "- Aucun ML, modele ML, backtest, strategie, signal, ordre ou trading.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "reports/current/latest_summary.md",
        "\n".join(
            [
                "# Latest Summary V8.4",
                "",
                "V8.3 est la derniere version validee par audit externe.",
                "",
                "V8.4 est la candidate courante. Elle assemble uniquement un dataset supervise offline OHLCV + aggTrades avec labels V5.2 filtres sur la fenetre V8.3 d'environ 1 an.",
                "",
                f"Fenetre : `{manifest['input_features_manifest']['window_start']}` -> `{manifest['input_features_manifest']['window_end']}`, `{manifest['input_features_manifest']['total_days']}` jours.",
                f"Colonnes features : `{manifest['feature_columns_count']}`.",
                "",
                "Aucun ML V8.4, aucun modele V8.4, aucun backtest, aucune strategie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading reel.",
                "",
                "V8.4 reste `pending_external_audit`.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "reports/PROJECT_STATE.md",
        "\n".join(
            [
                "# Etat du Projet : V8.3 validee + candidat V8.4",
                "",
                "- **Derniere version validee** : V8.3.",
                "- **Version candidate** : V8.4.",
                "- **Statut candidate** : `pending_external_audit`.",
                "- **Direction** : OHLCV + public trades 1-year offline supervised dataset preview.",
                "",
                "## V8.4",
                "",
                f"- Fenetre : `{manifest['input_features_manifest']['window_start']}` -> `{manifest['input_features_manifest']['window_end']}`.",
                f"- Total jours : `{manifest['input_features_manifest']['total_days']}`.",
                f"- Colonnes features : `{manifest['feature_columns_count']}`.",
                "- Aucun ML V8.4.",
                "- Aucun modele V8.4.",
                "- Aucun backtest, aucune strategie, aucun signal, aucun ordre, aucun trading reel.",
                "",
                "V8.4 reste non validee avant audit externe.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "README.md",
        "\n".join(
            [
                "# Projet Galapagos",
                "",
                "- Derniere version validee : V8.3.",
                "- Candidate : V8.4, OHLCV + public trades 1-year offline supervised dataset preview.",
                "",
                "V8.4 assemble uniquement un dataset supervise offline OHLCV + aggTrades Binance publiques avec labels V5.2 filtres sur la fenetre V8.3 d'environ 1 an.",
                "",
                "Aucun ML V8.4, aucun modele V8.4, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.",
                "",
                "## Commandes V8.4",
                "",
                "```bash",
                "python scripts/run_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py",
                "python scripts/validate_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py",
                "python -m pytest -q tests/datasets/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4.py",
                "python -m pytest -q tests/validation/test_ohlcv_trades_1y_offline_supervised_dataset_v8_4_validator.py",
                "python scripts/release_audit_lite_zip_v8_4.py",
                "python scripts/audit_audit_lite_zip_v8_4.py --zip projet-galapagos-v8.4-audit-lite.zip",
                "python scripts/smoke_audit_lite_zip_v8_4.py --zip projet-galapagos-v8.4-audit-lite.zip",
                "python -m pytest --collect-only -q",
                "```",
                "",
                "V8.4 reste `pending_external_audit` avant validation externe.",
            ]
        )
        + "\n",
    )


def _require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise RuntimeError(f"Missing {label} columns: {missing}")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
