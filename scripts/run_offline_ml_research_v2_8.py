from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.datasets.schemas import TARGET_TIMEFRAMES, get_dataset_gold_path, get_split_gold_path
from galapagos.datasets.validation import validate_offline_supervised_dataset_v2_7
from galapagos.features.validation import validate_causal_feature_store_v2_5
from galapagos.labels.validation import validate_label_factory_v2_6
from galapagos.ml.metrics import compute_classification_metrics
from galapagos.ml.quality import assess_ml_quality
from galapagos.ml.reports import build_ml_markdown
from galapagos.ml.schemas import (
    ALLOWED_FEATURE_COLUMNS_V2_8,
    CORRECTION_VERSION,
    EXPECTED_LIMITATIONS_V2_8,
    MANIFEST_PATH,
    MODEL_NAMES,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS_V2_8,
    SCORES_JSON_PATH,
    SCORES_MD_PATH,
    TARGET_NAME,
    VERSION,
    get_ml_score_path,
)
from galapagos.ml.training import build_model_scores
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4


def run_offline_ml_research_v2_8(root: Path = Path("."), ml_run_id: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    _validate_previous_layers(root)
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    if ml_run_id is None:
        ml_run_id = f"v2_8_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"

    input_datasets: dict[str, dict[str, Any]] = {}
    input_splits: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    sanity_checks: dict[str, dict[str, Any]] = {}
    all_scores = []

    for timeframe in TARGET_TIMEFRAMES:
        dataset_path = get_dataset_gold_path(root, timeframe)
        split_path = get_split_gold_path(root, timeframe)
        score_path = get_ml_score_path(root, timeframe)
        dataset = read_parquet(dataset_path)
        dataset_sha = sha256_file(dataset_path)
        split = read_parquet(split_path)
        scores = build_model_scores(dataset, dataset_sha256=dataset_sha, ml_run_id=ml_run_id)
        write_parquet(scores, score_path)
        all_scores.append(scores)
        score_sha = sha256_file(score_path)

        input_datasets[timeframe] = {"path": str(dataset_path.relative_to(root)), "sha256": dataset_sha, "rows": len(dataset)}
        input_splits[timeframe] = {"path": str(split_path.relative_to(root)), "sha256": sha256_file(split_path), "rows": len(split)}
        outputs[timeframe] = {
            "path": str(score_path.relative_to(root)),
            "sha256": score_sha,
            "bytes": score_path.stat().st_size,
            "rows": len(scores),
            "format": "parquet",
        }
        quality[timeframe] = assess_ml_quality(dataset, scores, timeframe)
        sanity_checks[timeframe] = {
            "train_rows": quality[timeframe]["train_rows"],
            "validation_rows": quality[timeframe]["validation_rows"],
            "test_rows": quality[timeframe]["test_rows"],
            "target_classes_seen_train": sorted(dataset[(dataset["split"] == "train") & (dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)][TARGET_NAME].dropna().astype(str).unique().tolist()),  # noqa: E712
            "target_classes_seen_validation": sorted(dataset[(dataset["split"] == "validation") & (dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)][TARGET_NAME].dropna().astype(str).unique().tolist()),  # noqa: E712
            "target_classes_seen_test": sorted(dataset[(dataset["split"] == "test") & (dataset["label_valid_h1"] == True) & (dataset["warmup_row"] == False)][TARGET_NAME].dropna().astype(str).unique().tolist()),  # noqa: E712
            "no_shuffle_confirmed": quality[timeframe]["no_shuffle_confirmed"],
            "forbidden_feature_columns_present": quality[timeframe]["forbidden_feature_columns_present"],
            "forbidden_output_columns_present": quality[timeframe]["forbidden_output_columns_present"],
        }

    import pandas as pd

    non_empty_scores = [frame for frame in all_scores if not frame.empty]
    all_scores_frame = pd.concat(non_empty_scores, ignore_index=True)
    metrics = compute_classification_metrics(all_scores_frame)
    manifest = {
        "version": VERSION,
        "correction_version": CORRECTION_VERSION,
        "status": "PASS",
        "created_at_utc": created_at,
        "ml_run_id": ml_run_id,
        "input_datasets": input_datasets,
        "input_splits": input_splits,
        "outputs": outputs,
        "target_name": TARGET_NAME,
        "feature_columns": ALLOWED_FEATURE_COLUMNS_V2_8,
        "models": MODEL_NAMES,
        "metrics": metrics,
        "sanity_checks": sanity_checks,
        "quality": quality,
        "safety": SAFETY_FLAGS_V2_8,
        "limitations": EXPECTED_LIMITATIONS_V2_8,
    }

    (root / MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REPORT_JSON_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / SCORES_JSON_PATH).parent.mkdir(parents=True, exist_ok=True)
    _write_json(root / MANIFEST_PATH, manifest)
    _write_json(root / REPORT_JSON_PATH, manifest)
    _write_json(
        root / SCORES_JSON_PATH,
        {"version": VERSION, "correction_version": CORRECTION_VERSION, "ml_run_id": ml_run_id, "outputs": outputs, "metrics": metrics},
    )
    markdown = build_ml_markdown(manifest)
    (root / REPORT_MD_PATH).write_text(markdown, encoding="utf-8")
    (root / SCORES_MD_PATH).write_text(markdown, encoding="utf-8")
    print("=== Galapagos V2.8 Offline ML Research ===")
    print("Status: PASS")
    print(f"ML run id: {ml_run_id}")
    for timeframe in TARGET_TIMEFRAMES:
        print(f"{timeframe}: score rows={outputs[timeframe]['rows']} used_rows={quality[timeframe]['rows_used_for_ml']}")
    return manifest


def _validate_previous_layers(root: Path) -> None:
    validators = [
        ("V2.3", validate_public_market_ingestion_v2_3(root)),
        ("V2.4", validate_ohlcv_resampling_v2_4(root)),
        ("V2.5", validate_causal_feature_store_v2_5(root)),
        ("V2.6", validate_label_factory_v2_6(root)),
        ("V2.7", validate_offline_supervised_dataset_v2_7(root)),
    ]
    for label, result in validators:
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed before V2.8: {result['errors']}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run_offline_ml_research_v2_8(Path("."))
