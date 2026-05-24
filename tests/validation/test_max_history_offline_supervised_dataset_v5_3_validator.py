from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.max_history_window import (
    build_max_history_offline_supervised_dataset_v5_3,
    build_split_frame_v5_3,
    input_feature_path,
    input_label_path,
    load_v5_1_feature_manifest,
    load_v5_2_label_manifest,
)
from galapagos.datasets.max_history_window_validation import (
    _find_forbidden_v5_3_artifacts,
    _validate_dataset_schema,
    _validate_dataset_temporal_rules,
    _validate_dataset_values_against_sources,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    _validate_split_frame,
    validate_max_history_offline_supervised_dataset_v5_3,
)
from galapagos.datasets.schemas import (
    DATACARD_MD_PATH_V5_3,
    MANIFEST_PATH_V5_3,
    REPORT_JSON_PATH_V5_3,
    REPORT_MD_PATH_V5_3,
    TIMEFRAMES_V5_3,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def valid_v5_3_template() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def feature_manifest(valid_v5_3_template: Path) -> dict[str, Any]:
    return load_v5_1_feature_manifest(valid_v5_3_template)


@pytest.fixture(scope="session")
def label_manifest(valid_v5_3_template: Path) -> dict[str, Any]:
    return load_v5_2_label_manifest(valid_v5_3_template)


@pytest.fixture(scope="session")
def valid_v5_3_validation_result(valid_v5_3_template: Path) -> dict[str, Any]:
    result = validate_max_history_offline_supervised_dataset_v5_3(valid_v5_3_template)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v5_3_manifest_report(valid_v5_3_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v5_3_template / MANIFEST_PATH_V5_3)), deepcopy(_load(valid_v5_3_template / REPORT_JSON_PATH_V5_3))


@pytest.fixture(scope="session")
def valid_v5_3_frame_cache(
    valid_v5_3_template: Path,
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
) -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    manifest = _load(valid_v5_3_template / MANIFEST_PATH_V5_3)
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]] = {}
    for timeframe in ["1h", "5m"]:
        feature_path = input_feature_path(valid_v5_3_template, timeframe, feature_manifest)
        label_path = input_label_path(valid_v5_3_template, timeframe, label_manifest)
        features = read_parquet(feature_path).head(2000).reset_index(drop=True)
        labels = read_parquet(label_path).head(2000).reset_index(drop=True)
        dataset = build_max_history_offline_supervised_dataset_v5_3(
            features,
            labels,
            feature_sha256=sha256_file(feature_path),
            label_sha256=sha256_file(label_path),
            dataset_run_id=manifest["dataset_run_id"],
        )
        splits = build_split_frame_v5_3(dataset)
        frames[timeframe] = (features, labels, dataset, splits)
    return frames


@pytest.fixture()
def valid_v5_3_frames(
    valid_v5_3_frame_cache: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    return {
        timeframe: (
            features.copy(deep=True),
            labels.copy(deep=True),
            dataset.copy(deep=True),
            splits.copy(deep=True),
        )
        for timeframe, (features, labels, dataset, splits) in valid_v5_3_frame_cache.items()
    }


def test_validator_v5_3_accepts_valid_dataset(valid_v5_3_validation_result: dict[str, Any]) -> None:
    assert valid_v5_3_validation_result["passed"] is True
    assert valid_v5_3_validation_result["errors"] == []


def test_validator_v5_3_rejects_extra_prediction_column_even_with_synced_checksum(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _assert_extra_column_rejected(valid_v5_3_frames, "prediction")


def test_validator_v5_3_rejects_extra_signal_column_even_with_synced_checksum(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _assert_extra_column_rejected(valid_v5_3_frames, "signal")


def test_validator_v5_3_rejects_extra_order_column_even_with_synced_checksum(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _assert_extra_column_rejected(valid_v5_3_frames, "order")


def test_validator_v5_3_rejects_column_order_mismatch_even_with_synced_checksum(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset, _splits = valid_v5_3_frames["1h"]
    columns = list(dataset.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors = _validate_dataset_schema(dataset[columns], "1h")
    assert _errors_contain(errors, "V5.3 dataset schema mismatch")


def test_validator_v5_3_rejects_wrong_source_features_sha256_even_with_synced_checksum(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, labels, dataset, _splits = valid_v5_3_frames["5m"]
    dataset["source_features_sha256"] = "bad"
    errors = _source_value_errors("5m", features, labels, dataset)
    assert _errors_contain(errors, "V5.3 dataset physical mismatch")


def test_validator_v5_3_rejects_wrong_source_labels_sha256_even_with_synced_checksum(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, labels, dataset, _splits = valid_v5_3_frames["1h"]
    dataset["source_labels_sha256"] = "bad"
    errors = _source_value_errors("1h", features, labels, dataset)
    assert _errors_contain(errors, "V5.3 dataset physical mismatch")


def test_validator_v5_3_rejects_modified_feature_value_even_with_synced_checksum(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, labels, dataset, _splits = valid_v5_3_frames["1h"]
    dataset.loc[40, "return_1"] = float(dataset.loc[40, "return_1"]) + 1.0
    errors = _source_value_errors("1h", features, labels, dataset)
    assert _errors_contain(errors, "V5.3 dataset physical mismatch")


def test_validator_v5_3_rejects_modified_label_value_even_with_synced_checksum(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, labels, dataset, _splits = valid_v5_3_frames["1h"]
    dataset.loc[40, "future_log_return_h3"] = float(dataset.loc[40, "future_log_return_h3"]) + 1.0
    errors = _source_value_errors("1h", features, labels, dataset)
    assert _errors_contain(errors, "V5.3 dataset physical mismatch")


def test_validator_v5_3_rejects_feature_available_ts_after_decision_ts(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset, _splits = valid_v5_3_frames["1h"]
    dataset.loc[0, "feature_available_ts"] = pd.Timestamp(dataset.loc[0, "decision_ts"]) + pd.Timedelta(minutes=1)
    errors = _validate_dataset_temporal_rules(dataset, "1h")
    assert _errors_contain(errors, "feature_available_ts > decision_ts")


def test_validator_v5_3_rejects_label_available_ts_before_or_equal_decision_ts(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset, _splits = valid_v5_3_frames["1h"]
    dataset.loc[0, "label_available_ts"] = dataset.loc[0, "decision_ts"]
    errors = _validate_dataset_temporal_rules(dataset, "1h")
    assert _errors_contain(errors, "label_available_ts <= decision_ts")


def test_validator_v5_3_rejects_temporally_shuffled_split(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset, _splits = valid_v5_3_frames["5m"]
    dataset.loc[0, "split"] = "test"
    dataset.loc[len(dataset) - 1, "split"] = "train"
    errors = _validate_dataset_temporal_rules(dataset, "5m")
    assert _errors_contain(errors, "split temporal order invalid")


def test_validator_v5_3_rejects_missing_walk_forward_group(
    valid_v5_3_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset, splits = valid_v5_3_frames["1h"]
    errors = _validate_split_frame(dataset, splits.drop(columns=["walk_forward_group"]), "1h")
    assert _errors_contain(errors, "V5.3 split schema mismatch")


def test_validator_v5_3_rejects_report_json_lie(valid_v5_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v5_3_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V5.3 quality report mismatch")


def test_validator_v5_3_rejects_manifest_unexpected_key(
    valid_v5_3_template: Path,
    feature_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
    valid_v5_3_manifest_report: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    manifest, _report = valid_v5_3_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(valid_v5_3_template, manifest, feature_manifest, label_manifest)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v5_3_rejects_report_unexpected_key(valid_v5_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v5_3_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v5_3_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v5_3_template: Path) -> None:
    _copy_markdown_set(tmp_path, valid_v5_3_template)
    (tmp_path / REPORT_MD_PATH_V5_3).write_text(
        (tmp_path / REPORT_MD_PATH_V5_3).read_text(encoding="utf-8") + "\nStrategy validated.\n",
        encoding="utf-8",
    )
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v5_3_rejects_datacard_strategy_validated_claim(tmp_path: Path, valid_v5_3_template: Path) -> None:
    _copy_markdown_set(tmp_path, valid_v5_3_template)
    (tmp_path / DATACARD_MD_PATH_V5_3).write_text(
        (tmp_path / DATACARD_MD_PATH_V5_3).read_text(encoding="utf-8") + "\nStrategy validated.\n",
        encoding="utf-8",
    )
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v5_3_rejects_safety_flag_ml_true(valid_v5_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_3_manifest_report, "ml_enabled")


def test_validator_v5_3_rejects_safety_flag_backtest_true(valid_v5_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_3_manifest_report, "backtest_enabled")


def test_validator_v5_3_rejects_safety_flag_trading_true(valid_v5_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_3_manifest_report, "trading_enabled")


def test_validator_v5_3_rejects_safety_flag_orders_true(valid_v5_3_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_3_manifest_report, "orders_enabled")


def test_validator_v5_3_rejects_model_file_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "models/model.pkl")
    errors = _find_forbidden_v5_3_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.3")


def test_validator_v5_3_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v5_3_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.3")


def test_validator_v5_3_allows_dataset_outputs_only_in_v5_3_paths(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v5_3/datasets/offline_supervised/dummy.txt")
    assert _find_forbidden_v5_3_artifacts(tmp_path) == []


def _assert_extra_column_rejected(
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]],
    column: str,
) -> None:
    _features, _labels, dataset, _splits = frames["1h"]
    dataset[column] = 0
    errors = _validate_dataset_schema(dataset, "1h")
    assert _errors_contain(errors, "V5.3 dataset schema mismatch")


def _source_value_errors(timeframe: str, features: pd.DataFrame, labels: pd.DataFrame, dataset: pd.DataFrame) -> list[str]:
    return _validate_dataset_values_against_sources(
        timeframe,
        dataset,
        features,
        labels,
        str(dataset["dataset_run_id"].iloc[0]),
        sha256_file(input_feature_path(ROOT, timeframe)),
        sha256_file(input_label_path(ROOT, timeframe)),
    )


def _assert_safety_flag_rejected(manifest_report: tuple[dict[str, Any], dict[str, Any]], flag: str) -> None:
    manifest, _report = manifest_report
    manifest["safety"][flag] = True
    errors = _validate_safety(manifest["safety"])
    assert _errors_contain(errors, f"V5.3 safety flag {flag} must be False")


def _copy_markdown_set(target_root: Path, source_root: Path) -> None:
    for relative in [REPORT_MD_PATH_V5_3, DATACARD_MD_PATH_V5_3, Path("docs/max_history_offline_supervised_dataset_v5_3.md")]:
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
