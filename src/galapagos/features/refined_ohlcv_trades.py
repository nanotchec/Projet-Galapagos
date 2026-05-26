from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.features.refined_ohlcv_trades_quality import assess_refined_ohlcv_trades_feature_quality_v9_0
from galapagos.features.refined_ohlcv_trades_schemas import (
    DOC_PATH_V9_0,
    EXPECTED_LIMITATIONS_V9_0,
    EXPECTED_ROWS_V9_0,
    FEATURE_AUDIT_MANIFEST_V8_9,
    FEATURE_SCHEMA_VERSION_V9_0,
    FEATURE_SELECTION_JSON_V8_9,
    INPUT_FEATURE_MANIFEST_V8_3,
    MANIFEST_PATH_V9_0,
    REFINED_OHLCV_TRADES_AUDIT_COLUMNS_V9_0,
    REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0,
    REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0,
    REPORT_JSON_PATH_V9_0,
    REPORT_MD_PATH_V9_0,
    SAFETY_FLAGS_V9_0,
    TIMEFRAMES_V9_0,
    TOTAL_DAYS_V9_0,
    VERSION_V9_0,
    WINDOW_END_V9_0,
    WINDOW_START_V9_0,
    get_refined_feature_path_v9_0,
)


def run_refined_ohlcv_trades_feature_store_v9_0(root: Path = Path(".")) -> dict[str, Any]:
    project_root = root.resolve()
    selection_report = _read_json(project_root / FEATURE_SELECTION_JSON_V8_9)
    audit_manifest = _read_json(project_root / FEATURE_AUDIT_MANIFEST_V8_9)
    input_manifest = _read_json(project_root / INPUT_FEATURE_MANIFEST_V8_3)
    selected_features = selection_report["candidate_refined_feature_set"]["selected_features"]
    if selected_features != REFINED_OHLCV_TRADES_SELECTED_FEATURES_V9_0:
        raise RuntimeError("V9.0 selected feature list no longer matches V8.9 selection report")

    created_at = utc_now_iso()
    feature_run_id = f"v9_0_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    selection_sha = sha256_file(project_root / FEATURE_SELECTION_JSON_V8_9)
    outputs: dict[str, dict[str, Any]] = {}
    input_features: dict[str, dict[str, Any]] = {}
    quality: dict[str, Any] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V9_0:
        source_path = project_root / input_manifest["outputs"][timeframe]["path"]
        source_sha = sha256_file(source_path)
        source = read_parquet(source_path)
        refined = build_refined_ohlcv_trades_features_v9_0(
            source,
            selected_features=selected_features,
            source_v8_3_features_sha256=source_sha,
            source_feature_selection_sha256=selection_sha,
            feature_run_id=feature_run_id,
        )
        output_path = get_refined_feature_path_v9_0(project_root, timeframe)
        write_parquet(refined, output_path)
        input_features[timeframe] = {
            "path": source_path.relative_to(project_root).as_posix(),
            "sha256": source_sha,
            "rows": int(len(source)),
        }
        outputs[timeframe] = {
            "path": output_path.relative_to(project_root).as_posix(),
            "sha256": sha256_file(output_path),
            "bytes": output_path.stat().st_size,
            "rows": int(len(refined)),
            "format": "parquet",
        }
        quality[timeframe] = assess_refined_ohlcv_trades_feature_quality_v9_0(
            refined,
            expected_rows=EXPECTED_ROWS_V9_0[timeframe],
            selected_features=selected_features,
        )
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V9_0,
        "status": status,
        "created_at_utc": created_at,
        "feature_run_id": feature_run_id,
        "input_feature_manifest_v8_3": {
            "path": INPUT_FEATURE_MANIFEST_V8_3.as_posix(),
            "sha256": sha256_file(project_root / INPUT_FEATURE_MANIFEST_V8_3),
            "window_start": input_manifest["window"]["window_start"],
            "window_end": input_manifest["window"]["window_end"],
            "total_days": int(input_manifest["window"]["total_days"]),
        },
        "input_feature_selection_v8_9": {
            "path": FEATURE_SELECTION_JSON_V8_9.as_posix(),
            "sha256": selection_sha,
            "selected_features_count": int(selection_report["candidate_refined_feature_set"]["selected_features_count"]),
            "dropped_features_count": int(selection_report["candidate_refined_feature_set"]["dropped_features_count"]),
            "review_features_count": int(selection_report["candidate_refined_feature_set"]["review_features_count"]),
        },
        "input_feature_audit_manifest_v8_9": {
            "path": FEATURE_AUDIT_MANIFEST_V8_9.as_posix(),
            "sha256": sha256_file(project_root / FEATURE_AUDIT_MANIFEST_V8_9),
            "leakage_guard_passed": bool(audit_manifest["leakage_guard"]["passed"]),
        },
        "window": {"window_start": WINDOW_START_V9_0, "window_end": WINDOW_END_V9_0, "total_days": TOTAL_DAYS_V9_0},
        "input_features": input_features,
        "outputs": outputs,
        "feature_schema_version": FEATURE_SCHEMA_VERSION_V9_0,
        "feature_columns": REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0,
        "selected_features": selected_features,
        "selected_features_count": len(selected_features),
        "dropped_features_absent": True,
        "review_features_excluded_by_default": True,
        "quality": quality,
        "safety": SAFETY_FLAGS_V9_0,
        "limitations": EXPECTED_LIMITATIONS_V9_0,
    }
    _write_json(project_root / MANIFEST_PATH_V9_0, manifest)
    _write_json(project_root / REPORT_JSON_PATH_V9_0, manifest)
    markdown = build_refined_feature_store_markdown_v9_0(manifest)
    _write_text(project_root / REPORT_MD_PATH_V9_0, markdown)
    _write_text(project_root / DOC_PATH_V9_0, markdown)
    return manifest


def build_refined_ohlcv_trades_features_v9_0(
    source: pd.DataFrame,
    *,
    selected_features: list[str],
    source_v8_3_features_sha256: str,
    source_feature_selection_sha256: str,
    feature_run_id: str,
) -> pd.DataFrame:
    required = [
        "source",
        "venue",
        "market_type",
        "symbol",
        "timeframe",
        "event_ts",
        "close_ts",
        "available_ts",
        "decision_ts",
        "feature_available_ts",
        "source_ohlcv_sha256",
        "source_trades_manifest_sha256",
        "trade_source_type",
        "warmup_row",
        *selected_features,
    ]
    missing = [column for column in required if column not in source.columns]
    if missing:
        raise RuntimeError(f"V9.0 source V8.3 features missing required columns: {missing}")
    frame = source.sort_values("event_ts").reset_index(drop=True).copy()
    refined = frame[
        [
            "source",
            "venue",
            "market_type",
            "symbol",
            "timeframe",
            "event_ts",
            "close_ts",
            "available_ts",
            "decision_ts",
            "feature_available_ts",
            "source_ohlcv_sha256",
            "source_trades_manifest_sha256",
            "trade_source_type",
            *selected_features,
            "warmup_row",
        ]
    ].copy()
    refined["feature_run_id"] = feature_run_id
    refined["source_v8_3_features_sha256"] = source_v8_3_features_sha256
    refined["source_feature_selection_sha256"] = source_feature_selection_sha256
    refined["feature_schema_version"] = FEATURE_SCHEMA_VERSION_V9_0
    refined["refined_feature_null_count"] = refined[selected_features].isna().sum(axis=1).astype("int16")
    numeric = refined[selected_features].apply(pd.to_numeric, errors="coerce")
    refined["refined_feature_error_count"] = np.isinf(numeric).sum(axis=1).astype("int16")
    return refined[REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0].copy()


def build_refined_feature_store_markdown_v9_0(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        f"- `{timeframe}` : `{payload['rows']}` lignes, `{payload['path']}`."
        for timeframe, payload in manifest["outputs"].items()
    )
    return "\n".join(
        [
            "# Refined OHLCV + trades feature store V9.0",
            "",
            "V9.0 produit une feature store raffinee a partir de V8.3 et de la selection V8.9.",
            "",
            f"- Selected features : `{manifest['selected_features_count']}`.",
            f"- Fenetre : `{manifest['window']['window_start']}` -> `{manifest['window']['window_end']}`.",
            "",
            "## Outputs",
            "",
            rows,
            "",
            "## Securite",
            "",
            "- V9.0 ne produit aucun label.",
            "- V9.0 ne produit aucun dataset ML.",
            "- V9.0 ne produit aucun modele ML.",
            "- V9.0 ne produit aucun backtest.",
            "- V9.0 ne produit aucune strategie.",
            "- V9.0 ne produit aucun signal de trading.",
            "- V9.0 ne produit aucun ordre.",
            "- V9.0 n'autorise aucun paper live ni trading reel.",
        ]
    ) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
