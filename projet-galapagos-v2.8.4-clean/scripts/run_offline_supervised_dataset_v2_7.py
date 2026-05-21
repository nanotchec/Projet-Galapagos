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
from galapagos.datasets.assembly import build_offline_supervised_dataset
from galapagos.datasets.datacard import build_datacard_markdown, build_quality_markdown
from galapagos.datasets.quality import assess_dataset_quality
from galapagos.datasets.schemas import (
    DATASET_COLUMNS_V2_7,
    DATASET_SCHEMA_VERSION,
    DATACARD_MD_PATH,
    EXPECTED_LIMITATIONS_V2_7,
    EXPECTED_ROWS_BY_TIMEFRAME,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SPLIT_POLICY_V2_7,
    TARGET_TIMEFRAMES,
    VERSION,
    get_dataset_gold_path,
    get_split_gold_path,
)
from galapagos.datasets.splits import build_split_frame
from galapagos.features.registry import get_feature_gold_path
from galapagos.features.validation import validate_causal_feature_store_v2_5
from galapagos.labels.registry import get_label_gold_path
from galapagos.labels.validation import validate_label_factory_v2_6
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
from galapagos.validation.resampling import validate_ohlcv_resampling_v2_4


def run_offline_supervised_dataset_v2_7(root: Path = Path("."), dataset_run_id: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    _validate_previous_layers(root)

    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    if dataset_run_id is None:
        dataset_run_id = f"v2_7_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"

    input_features: dict[str, dict[str, Any]] = {}
    input_labels: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    splits: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}

    status = "PASS"
    for timeframe in TARGET_TIMEFRAMES:
        feature_path = get_feature_gold_path(root, timeframe)
        label_path = get_label_gold_path(root, timeframe)
        dataset_path = get_dataset_gold_path(root, timeframe)
        split_path = get_split_gold_path(root, timeframe)

        features = read_parquet(feature_path)
        labels = read_parquet(label_path)
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)

        dataset = build_offline_supervised_dataset(
            features,
            labels,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=dataset_run_id,
        )
        split_frame = build_split_frame(dataset)
        write_parquet(dataset, dataset_path)
        write_parquet(split_frame, split_path)

        input_features[timeframe] = {
            "path": str(feature_path.relative_to(root)),
            "sha256": feature_sha,
            "rows": int(len(features)),
        }
        input_labels[timeframe] = {
            "path": str(label_path.relative_to(root)),
            "sha256": label_sha,
            "rows": int(len(labels)),
        }
        outputs[timeframe] = {
            "path": str(dataset_path.relative_to(root)),
            "sha256": sha256_file(dataset_path),
            "bytes": dataset_path.stat().st_size,
            "rows": int(len(dataset)),
            "format": "parquet",
        }
        splits[timeframe] = {
            "path": str(split_path.relative_to(root)),
            "sha256": sha256_file(split_path),
            "bytes": split_path.stat().st_size,
            "rows": int(len(split_frame)),
            "format": "parquet",
        }

        assessment = assess_dataset_quality(
            dataset,
            expected_rows=EXPECTED_ROWS_BY_TIMEFRAME[timeframe],
            timeframe=timeframe,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
        )
        quality[timeframe] = assessment
        if assessment["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION,
        "status": status,
        "created_at_utc": created_at,
        "dataset_run_id": dataset_run_id,
        "input_features": input_features,
        "input_labels": input_labels,
        "outputs": outputs,
        "splits": splits,
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "dataset_columns": DATASET_COLUMNS_V2_7,
        "split_policy": SPLIT_POLICY_V2_7,
        "quality": quality,
        "safety": {
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
        },
        "limitations": EXPECTED_LIMITATIONS_V2_7,
    }

    _write_json(root / MANIFEST_PATH, manifest)
    _write_json(root / REPORT_JSON_PATH, manifest)
    _write_text(root / REPORT_MD_PATH, build_quality_markdown(manifest))
    _write_text(root / DATACARD_MD_PATH, build_datacard_markdown(manifest))
    return manifest


def _validate_previous_layers(root: Path) -> None:
    checks = [
        ("V2.3.1 ingestion", validate_public_market_ingestion_v2_3(root)),
        ("V2.4.8 resampling", validate_ohlcv_resampling_v2_4(root)),
        ("V2.5.2 features", validate_causal_feature_store_v2_5(root)),
        ("V2.6.2 labels", validate_label_factory_v2_6(root)),
    ]
    for label, result in checks:
        if not result["passed"]:
            raise RuntimeError(f"{label} validation failed: {result['errors']}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    manifest = run_offline_supervised_dataset_v2_7(Path("."))
    print("=== Galapagos V2.7 Offline Supervised Dataset Assembly ===")
    print(f"Status: {manifest['status']}")
    print(f"Dataset run id: {manifest['dataset_run_id']}")
    for timeframe in TARGET_TIMEFRAMES:
        print(
            f"{timeframe}: dataset={manifest['outputs'][timeframe]['rows']} rows, "
            f"splits={manifest['quality'][timeframe]['split_counts']}"
        )


if __name__ == "__main__":
    main()
