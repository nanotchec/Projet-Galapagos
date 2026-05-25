from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.ohlcv_trades_window import (
    build_ohlcv_trades_offline_supervised_dataset_v7_3,
    build_split_frame_v7_3,
    filter_labels_to_v7_3_window,
    input_feature_path,
    input_label_path,
    load_v5_2_label_manifest,
    load_v7_2_feature_manifest,
)
from galapagos.datasets.ohlcv_trades_window_quality import assess_ohlcv_trades_dataset_quality_v7_3
from galapagos.datasets.ohlcv_trades_window_validation import (
    _find_forbidden_v7_3_artifacts,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    validate_dataset_schema_v7_3,
    validate_dataset_source_value_equality_v7_3,
    validate_dataset_values_against_sources_v7_3,
    validate_ohlcv_trades_offline_supervised_dataset_v7_3,
    validate_split_frame_v7_3,
)
from galapagos.datasets.schemas import (
    DATACARD_MD_PATH_V7_3,
    DOC_PATH_V7_3,
    EXPECTED_ROWS_V7_3,
    MANIFEST_PATH_V7_3,
    REPORT_JSON_PATH_V7_3,
    REPORT_MD_PATH_V7_3,
    SPLIT_COLUMNS_V7_3,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def feature_manifest() -> dict[str, Any]:
    return load_v7_2_feature_manifest(ROOT)


@pytest.fixture(scope="session")
def label_manifest() -> dict[str, Any]:
    return load_v5_2_label_manifest(ROOT)


@pytest.fixture(scope="session")
def valid_v7_3_validation_result() -> dict[str, Any]:
    result = validate_ohlcv_trades_offline_supervised_dataset_v7_3(ROOT)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v7_3_manifest_report() -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(ROOT / MANIFEST_PATH_V7_3)), deepcopy(_load(ROOT / REPORT_JSON_PATH_V7_3))


@pytest.fixture(scope="session")
def valid_v7_3_frame_cache(
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
) -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]:
    manifest = _load(ROOT / MANIFEST_PATH_V7_3)
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]] = {}
    for timeframe in ["1h", "5m"]:
        feature_path = input_feature_path(ROOT, timeframe, feature_manifest)
        label_path = input_label_path(ROOT, timeframe, label_manifest)
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)
        features = read_parquet(feature_path).head(2000).reset_index(drop=True)
        labels = filter_labels_to_v7_3_window(read_parquet(label_path)).head(2000).reset_index(drop=True)
        dataset = build_ohlcv_trades_offline_supervised_dataset_v7_3(
            features,
            labels,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=manifest["dataset_run_id"],
        )
        splits = build_split_frame_v7_3(dataset)
        frames[timeframe] = (features, labels, dataset, splits, feature_sha, label_sha)
    return frames


@pytest.fixture()
def valid_v7_3_frames(
    valid_v7_3_frame_cache: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]:
    return {
        timeframe: (
            features.copy(deep=True),
            labels.copy(deep=True),
            dataset.copy(deep=True),
            splits.copy(deep=True),
            feature_sha,
            label_sha,
        )
        for timeframe, (features, labels, dataset, splits, feature_sha, label_sha) in valid_v7_3_frame_cache.items()
    }


def test_validator_v7_3_accepts_valid_dataset(valid_v7_3_validation_result: dict[str, Any]) -> None:
    assert valid_v7_3_validation_result["passed"] is True
    assert valid_v7_3_validation_result["errors"] == []


def test_validator_v7_3_rejects_extra_prediction_column_even_with_synced_checksum(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _assert_extra_column_rejected(valid_v7_3_frames, "prediction")


def test_validator_v7_3_rejects_extra_trading_signal_column_even_with_synced_checksum(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _assert_extra_column_rejected(valid_v7_3_frames, "trading_signal")


def test_validator_v7_3_rejects_extra_order_column_even_with_synced_checksum(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _assert_extra_column_rejected(valid_v7_3_frames, "order")


def test_validator_v7_3_rejects_column_order_mismatch_even_with_synced_checksum(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _features, _labels, dataset, _splits, _feature_sha, _label_sha = valid_v7_3_frames["1h"]
    columns = list(dataset.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors = validate_dataset_schema_v7_3(dataset[columns], "1h")
    assert _contains(errors, "V7.3 dataset schema mismatch")


def test_validator_v7_3_rejects_wrong_source_features_sha256_even_with_synced_checksum(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, feature_sha, label_sha = valid_v7_3_frames["5m"]
    dataset["source_features_sha256"] = "bad"
    errors = _source_value_errors("5m", features, labels, dataset, feature_sha, label_sha)
    assert _contains(errors, "source_features_sha256 mismatch")


def test_validator_v7_3_rejects_wrong_source_labels_sha256_even_with_synced_checksum(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, feature_sha, label_sha = valid_v7_3_frames["1h"]
    dataset["source_labels_sha256"] = "bad"
    errors = _source_value_errors("1h", features, labels, dataset, feature_sha, label_sha)
    assert _contains(errors, "source_labels_sha256 mismatch")


def test_validator_v7_3_rejects_modified_feature_value_even_with_synced_checksum(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, _feature_sha, _label_sha = valid_v7_3_frames["1h"]
    dataset.loc[100, "agg_trade_count"] = int(dataset.loc[100, "agg_trade_count"]) + 1
    errors = validate_dataset_source_value_equality_v7_3("1h", dataset, features, labels)
    assert _contains(errors, "feature values changed")


def test_validator_v7_3_rejects_modified_label_value_even_with_synced_checksum(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, _feature_sha, _label_sha = valid_v7_3_frames["1h"]
    dataset.loc[100, "future_log_return_h3"] = float(dataset.loc[100, "future_log_return_h3"]) + 1.0
    errors = validate_dataset_source_value_equality_v7_3("1h", dataset, features, labels)
    assert _contains(errors, "label values changed")


def test_validator_v7_3_rejects_feature_available_ts_after_decision_ts(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, feature_sha, label_sha = valid_v7_3_frames["1h"]
    dataset.loc[0, "feature_available_ts"] = pd.Timestamp(dataset.loc[0, "decision_ts"]) + pd.Timedelta(minutes=1)
    errors = _source_value_errors("1h", features, labels, dataset, feature_sha, label_sha)
    assert _contains(errors, "feature_available_ts > decision_ts")


def test_validator_v7_3_rejects_label_available_ts_before_or_equal_decision_ts(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, feature_sha, label_sha = valid_v7_3_frames["1h"]
    dataset.loc[0, "label_available_ts"] = dataset.loc[0, "decision_ts"]
    errors = _source_value_errors("1h", features, labels, dataset, feature_sha, label_sha)
    assert _contains(errors, "label_available_ts <= decision_ts")


def test_validator_v7_3_rejects_temporally_shuffled_split(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _features, _labels, dataset, _splits, feature_sha, label_sha = valid_v7_3_frames["5m"]
    dataset.loc[0, "split"] = "test"
    dataset.loc[len(dataset) - 1, "split"] = "train"
    quality = assess_ohlcv_trades_dataset_quality_v7_3(
        dataset,
        dataset[SPLIT_COLUMNS_V7_3],
        expected_rows=EXPECTED_ROWS_V7_3["5m"],
        timeframe="5m",
        feature_sha256=feature_sha,
        label_sha256=label_sha,
    )
    assert _contains(quality["errors"], "split temporal order invalid")


def test_validator_v7_3_rejects_missing_walk_forward_group(
    valid_v7_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _features, _labels, dataset, splits, _feature_sha, _label_sha = valid_v7_3_frames["1h"]
    errors = validate_split_frame_v7_3(dataset, splits.drop(columns=["walk_forward_group"]), "1h")
    assert _contains(errors, "V7.3 split schema mismatch")


def test_validator_v7_3_rejects_report_json_lie(valid_v7_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v7_3_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _contains(errors, "deterministic projection")


def test_validator_v7_3_rejects_manifest_unexpected_key(
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
    valid_v7_3_manifest_report: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    manifest, _report = valid_v7_3_manifest_report
    manifest["unexpected"] = True
    errors = _validate_manifest_structure(ROOT, manifest, feature_manifest, label_manifest)
    assert _contains(errors, "unexpected keys")


def test_validator_v7_3_rejects_report_unexpected_key(valid_v7_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v7_3_manifest_report
    report["unexpected"] = "value"
    errors = _validate_report(manifest, report)
    assert _contains(errors, "unexpected keys")


def test_validator_v7_3_rejects_markdown_strategy_validated_claim(tmp_path: Path) -> None:
    _copy_markdown_set(tmp_path)
    (tmp_path / REPORT_MD_PATH_V7_3).write_text(
        (tmp_path / REPORT_MD_PATH_V7_3).read_text(encoding="utf-8") + "\nStrategy validated.\n",
        encoding="utf-8",
    )
    assert _contains(_validate_markdown(tmp_path), "forbidden claim")


def test_validator_v7_3_rejects_datacard_strategy_validated_claim(tmp_path: Path) -> None:
    _copy_markdown_set(tmp_path)
    (tmp_path / DATACARD_MD_PATH_V7_3).write_text(
        (tmp_path / DATACARD_MD_PATH_V7_3).read_text(encoding="utf-8") + "\nStrategy validated.\n",
        encoding="utf-8",
    )
    assert _contains(_validate_markdown(tmp_path), "forbidden claim")


def test_validator_v7_3_rejects_safety_flag_ml_true(valid_v7_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v7_3_manifest_report, "ml_enabled")


def test_validator_v7_3_rejects_safety_flag_backtest_true(valid_v7_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v7_3_manifest_report, "backtest_enabled")


def test_validator_v7_3_rejects_safety_flag_trading_true(valid_v7_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v7_3_manifest_report, "trading_enabled")


def test_validator_v7_3_rejects_safety_flag_orders_true(valid_v7_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v7_3_manifest_report, "orders_enabled")


def test_validator_v7_3_rejects_model_file_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "models/model.pkl")
    assert _contains(_find_forbidden_v7_3_artifacts(tmp_path), "Forbidden V7.3")


def test_validator_v7_3_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    assert _contains(_find_forbidden_v7_3_artifacts(tmp_path), "Forbidden V7.3")


def test_validator_v7_3_allows_dataset_outputs_only_in_v7_3_paths(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v7_3/datasets/offline_supervised_ohlcv_trades/dummy.txt")
    assert _find_forbidden_v7_3_artifacts(tmp_path) == []


def _assert_extra_column_rejected(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]],
    column: str,
) -> None:
    _features, _labels, dataset, _splits, _feature_sha, _label_sha = frames["1h"]
    dataset[column] = 0
    errors = validate_dataset_schema_v7_3(dataset, "1h")
    assert _contains(errors, "V7.3 dataset schema mismatch")


def _source_value_errors(
    timeframe: str,
    features: pd.DataFrame,
    labels: pd.DataFrame,
    dataset: pd.DataFrame,
    feature_sha: str,
    label_sha: str,
) -> list[str]:
    return validate_dataset_values_against_sources_v7_3(
        timeframe,
        dataset,
        features,
        labels,
        str(dataset["dataset_run_id"].iloc[0]),
        feature_sha,
        label_sha,
    )


def _assert_safety_flag_rejected(manifest_report: tuple[dict[str, Any], dict[str, Any]], flag: str) -> None:
    manifest, _report = manifest_report
    manifest["safety"][flag] = True
    errors = _validate_safety(manifest["safety"])
    assert _contains(errors, flag)


def _copy_markdown_set(target_root: Path) -> None:
    for relative in [REPORT_MD_PATH_V7_3, DATACARD_MD_PATH_V7_3, DOC_PATH_V7_3]:
        destination = target_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text((ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("forbidden", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _contains(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
