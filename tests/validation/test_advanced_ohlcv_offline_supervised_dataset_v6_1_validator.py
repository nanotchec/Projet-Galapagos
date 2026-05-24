from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.advanced_ohlcv_window import (
    build_advanced_ohlcv_offline_supervised_dataset_v6_1,
    build_split_frame_v6_1,
    input_feature_path,
    input_label_path,
    load_v5_2_label_manifest,
    load_v6_0_feature_manifest,
)
from galapagos.datasets.advanced_ohlcv_window_quality import assess_advanced_ohlcv_dataset_quality
from galapagos.datasets.advanced_ohlcv_window_validation import (
    _find_forbidden_v6_1_artifacts,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    validate_advanced_ohlcv_offline_supervised_dataset_v6_1,
    validate_dataset_schema_v6_1,
    validate_dataset_source_value_equality_v6_1,
    validate_dataset_values_against_sources_v6_1,
    validate_split_frame_v6_1,
)
from galapagos.datasets.schemas import (
    DATACARD_MD_PATH_V6_1,
    MANIFEST_PATH_V6_1,
    REPORT_JSON_PATH_V6_1,
    REPORT_MD_PATH_V6_1,
    SPLIT_COLUMNS_V6_1,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def valid_v6_1_template() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def feature_manifest(valid_v6_1_template: Path) -> dict[str, Any]:
    return load_v6_0_feature_manifest(valid_v6_1_template)


@pytest.fixture(scope="session")
def label_manifest(valid_v6_1_template: Path) -> dict[str, Any]:
    return load_v5_2_label_manifest(valid_v6_1_template)


@pytest.fixture(scope="session")
def valid_v6_1_validation_result(valid_v6_1_template: Path) -> dict[str, Any]:
    result = validate_advanced_ohlcv_offline_supervised_dataset_v6_1(valid_v6_1_template)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v6_1_manifest_report(valid_v6_1_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v6_1_template / MANIFEST_PATH_V6_1)), deepcopy(_load(valid_v6_1_template / REPORT_JSON_PATH_V6_1))


@pytest.fixture(scope="session")
def valid_v6_1_frame_cache(
    valid_v6_1_template: Path,
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
) -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]:
    manifest = _load(valid_v6_1_template / MANIFEST_PATH_V6_1)
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]] = {}
    for timeframe in ["1h", "5m"]:
        feature_path = input_feature_path(valid_v6_1_template, timeframe, feature_manifest)
        label_path = input_label_path(valid_v6_1_template, timeframe, label_manifest)
        feature_sha = sha256_file(feature_path)
        label_sha = sha256_file(label_path)
        features = read_parquet(feature_path).head(2000).reset_index(drop=True)
        labels = read_parquet(label_path).head(2000).reset_index(drop=True)
        dataset = build_advanced_ohlcv_offline_supervised_dataset_v6_1(
            features,
            labels,
            feature_sha256=feature_sha,
            label_sha256=label_sha,
            dataset_run_id=manifest["dataset_run_id"],
        )
        splits = build_split_frame_v6_1(dataset)
        frames[timeframe] = (features, labels, dataset, splits, feature_sha, label_sha)
    return frames


@pytest.fixture()
def valid_v6_1_frames(
    valid_v6_1_frame_cache: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
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
        for timeframe, (features, labels, dataset, splits, feature_sha, label_sha) in valid_v6_1_frame_cache.items()
    }


def test_validator_v6_1_accepts_valid_dataset(valid_v6_1_validation_result: dict[str, Any]) -> None:
    assert valid_v6_1_validation_result["passed"] is True
    assert valid_v6_1_validation_result["errors"] == []


def test_validator_v6_1_accepts_macd_like_signal_feature(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _features, _labels, dataset, _splits, _feature_sha, _label_sha = valid_v6_1_frames["1h"]
    assert "macd_like_signal" in dataset.columns
    assert validate_dataset_schema_v6_1(dataset, "1h") == []


def test_validator_v6_1_rejects_extra_prediction_column_even_with_synced_checksum(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _assert_extra_column_rejected(valid_v6_1_frames, "prediction")


def test_validator_v6_1_rejects_extra_trading_signal_column_even_with_synced_checksum(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _assert_extra_column_rejected(valid_v6_1_frames, "trading_signal")


def test_validator_v6_1_rejects_extra_order_column_even_with_synced_checksum(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _assert_extra_column_rejected(valid_v6_1_frames, "order")


def test_validator_v6_1_rejects_column_order_mismatch_even_with_synced_checksum(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _features, _labels, dataset, _splits, _feature_sha, _label_sha = valid_v6_1_frames["1h"]
    columns = list(dataset.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors = validate_dataset_schema_v6_1(dataset[columns], "1h")
    assert _errors_contain(errors, "V6.1 dataset schema mismatch")


def test_validator_v6_1_rejects_wrong_source_features_sha256_even_with_synced_checksum(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, feature_sha, label_sha = valid_v6_1_frames["5m"]
    dataset["source_features_sha256"] = "bad"
    errors = _source_value_errors("5m", features, labels, dataset, feature_sha, label_sha)
    assert _errors_contain(errors, "source_features_sha256 mismatch")


def test_validator_v6_1_rejects_wrong_source_labels_sha256_even_with_synced_checksum(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, feature_sha, label_sha = valid_v6_1_frames["1h"]
    dataset["source_labels_sha256"] = "bad"
    errors = _source_value_errors("1h", features, labels, dataset, feature_sha, label_sha)
    assert _errors_contain(errors, "source_labels_sha256 mismatch")


def test_validator_v6_1_rejects_modified_feature_value_even_with_synced_checksum(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, _feature_sha, _label_sha = valid_v6_1_frames["1h"]
    dataset.loc[140, "return_1"] = float(dataset.loc[140, "return_1"]) + 1.0
    errors = validate_dataset_source_value_equality_v6_1("1h", dataset, features, labels)
    assert _errors_contain(errors, "dataset feature source mismatch")


def test_validator_v6_1_rejects_modified_label_value_even_with_synced_checksum(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, _feature_sha, _label_sha = valid_v6_1_frames["1h"]
    dataset.loc[140, "future_log_return_h3"] = float(dataset.loc[140, "future_log_return_h3"]) + 1.0
    errors = validate_dataset_source_value_equality_v6_1("1h", dataset, features, labels)
    assert _errors_contain(errors, "dataset label source mismatch")


def test_validator_v6_1_rejects_feature_available_ts_after_decision_ts(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, feature_sha, label_sha = valid_v6_1_frames["1h"]
    dataset.loc[0, "feature_available_ts"] = pd.Timestamp(dataset.loc[0, "decision_ts"]) + pd.Timedelta(minutes=1)
    errors = _source_value_errors("1h", features, labels, dataset, feature_sha, label_sha)
    assert _errors_contain(errors, "feature_available_ts > decision_ts")


def test_validator_v6_1_rejects_label_available_ts_before_or_equal_decision_ts(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    features, labels, dataset, _splits, feature_sha, label_sha = valid_v6_1_frames["1h"]
    dataset.loc[0, "label_available_ts"] = dataset.loc[0, "decision_ts"]
    errors = _source_value_errors("1h", features, labels, dataset, feature_sha, label_sha)
    assert _errors_contain(errors, "label_available_ts <= decision_ts")


def test_validator_v6_1_rejects_temporally_shuffled_split(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _features, _labels, dataset, _splits, feature_sha, label_sha = valid_v6_1_frames["5m"]
    dataset.loc[0, "split"] = "test"
    dataset.loc[len(dataset) - 1, "split"] = "train"
    quality = assess_advanced_ohlcv_dataset_quality(
        dataset,
        dataset[SPLIT_COLUMNS_V6_1],
        expected_rows=len(dataset),
        timeframe="5m",
        feature_sha256=feature_sha,
        label_sha256=label_sha,
    )
    assert _errors_contain(quality["errors"], "split temporal order invalid")


def test_validator_v6_1_rejects_missing_walk_forward_group(
    valid_v6_1_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]]
) -> None:
    _features, _labels, dataset, splits, _feature_sha, _label_sha = valid_v6_1_frames["1h"]
    errors = validate_split_frame_v6_1(dataset, splits.drop(columns=["walk_forward_group"]), "1h")
    assert _errors_contain(errors, "V6.1 split schema mismatch")


def test_validator_v6_1_rejects_report_json_lie(valid_v6_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v6_1_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V6.1 quality report outputs mismatch")


def test_validator_v6_1_rejects_manifest_unexpected_key(
    valid_v6_1_template: Path,
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
    valid_v6_1_manifest_report: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    manifest, _report = valid_v6_1_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(valid_v6_1_template, manifest, feature_manifest, label_manifest)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v6_1_rejects_report_unexpected_key(valid_v6_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v6_1_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v6_1_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v6_1_template: Path) -> None:
    _copy_markdown_set(tmp_path, valid_v6_1_template)
    (tmp_path / REPORT_MD_PATH_V6_1).write_text(
        (tmp_path / REPORT_MD_PATH_V6_1).read_text(encoding="utf-8") + "\nStrategy validated.\n",
        encoding="utf-8",
    )
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v6_1_rejects_datacard_strategy_validated_claim(tmp_path: Path, valid_v6_1_template: Path) -> None:
    _copy_markdown_set(tmp_path, valid_v6_1_template)
    (tmp_path / DATACARD_MD_PATH_V6_1).write_text(
        (tmp_path / DATACARD_MD_PATH_V6_1).read_text(encoding="utf-8") + "\nStrategy validated.\n",
        encoding="utf-8",
    )
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v6_1_rejects_safety_flag_ml_true(valid_v6_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v6_1_manifest_report, "ml_enabled")


def test_validator_v6_1_rejects_safety_flag_backtest_true(valid_v6_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v6_1_manifest_report, "backtest_enabled")


def test_validator_v6_1_rejects_safety_flag_trading_true(valid_v6_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v6_1_manifest_report, "trading_enabled")


def test_validator_v6_1_rejects_safety_flag_orders_true(valid_v6_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v6_1_manifest_report, "orders_enabled")


def test_validator_v6_1_rejects_model_file_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "models/model.pkl")
    errors = _find_forbidden_v6_1_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V6.1")


def test_validator_v6_1_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v6_1_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V6.1")


def test_validator_v6_1_allows_dataset_outputs_only_in_v6_1_paths(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v6_1/datasets/offline_supervised_advanced_ohlcv/dummy.txt")
    assert _find_forbidden_v6_1_artifacts(tmp_path) == []


def _assert_extra_column_rejected(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]],
    column: str,
) -> None:
    _features, _labels, dataset, _splits, _feature_sha, _label_sha = frames["1h"]
    dataset[column] = 0
    errors = validate_dataset_schema_v6_1(dataset, "1h")
    assert _errors_contain(errors, "V6.1 dataset schema mismatch")


def _source_value_errors(
    timeframe: str,
    features: pd.DataFrame,
    labels: pd.DataFrame,
    dataset: pd.DataFrame,
    feature_sha: str,
    label_sha: str,
) -> list[str]:
    return validate_dataset_values_against_sources_v6_1(
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
    assert _errors_contain(errors, f"V6.1 safety flag {flag} must be false")


def _copy_markdown_set(target_root: Path, source_root: Path) -> None:
    for relative in [REPORT_MD_PATH_V6_1, DATACARD_MD_PATH_V6_1, Path("docs/advanced_ohlcv_offline_supervised_dataset_v6_1.md")]:
        destination = target_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text((source_root / relative).read_text(encoding="utf-8"), encoding="utf-8")


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("forbidden", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
