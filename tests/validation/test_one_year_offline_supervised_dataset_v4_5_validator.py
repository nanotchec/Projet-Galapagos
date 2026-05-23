from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.datasets.one_year_window import input_feature_path, input_label_path
from galapagos.datasets.one_year_window_validation import (
    _find_forbidden_v4_5_artifacts,
    _validate_dataset_schema,
    _validate_dataset_temporal_rules,
    _validate_dataset_values_against_sources,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    validate_one_year_offline_supervised_dataset_v4_5,
)
from galapagos.datasets.schemas import (
    DATACARD_MD_PATH_V4_5,
    MANIFEST_PATH_V4_5,
    REPORT_JSON_PATH_V4_5,
    REPORT_MD_PATH_V4_5,
    TIMEFRAMES_V4_5,
    get_dataset_v4_5_path,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def valid_v4_5_template() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def valid_v4_5_validation_result(valid_v4_5_template: Path) -> dict[str, Any]:
    result = validate_one_year_offline_supervised_dataset_v4_5(valid_v4_5_template)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v4_5_manifest_report(valid_v4_5_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v4_5_template / MANIFEST_PATH_V4_5)), deepcopy(_load(valid_v4_5_template / REPORT_JSON_PATH_V4_5))


@pytest.fixture(scope="session")
def valid_v4_5_frame_cache(valid_v4_5_template: Path) -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]] = {}
    for timeframe in TIMEFRAMES_V4_5:
        features = read_parquet(input_feature_path(valid_v4_5_template, timeframe))
        labels = read_parquet(input_label_path(valid_v4_5_template, timeframe))
        dataset = read_parquet(get_dataset_v4_5_path(valid_v4_5_template, timeframe))
        frames[timeframe] = (features, labels, dataset)
    return frames


@pytest.fixture()
def valid_v4_5_frames(
    valid_v4_5_frame_cache: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    return {
        timeframe: (features.copy(deep=True), labels.copy(deep=True), dataset.copy(deep=True))
        for timeframe, (features, labels, dataset) in valid_v4_5_frame_cache.items()
    }


def test_validator_v4_5_accepts_valid_dataset(valid_v4_5_validation_result: dict[str, Any]) -> None:
    assert valid_v4_5_validation_result["passed"] is True
    assert valid_v4_5_validation_result["errors"] == []


def test_validator_v4_5_rejects_extra_prediction_column_even_with_synced_checksum(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _assert_extra_column_rejected(valid_v4_5_frames, "prediction")


def test_validator_v4_5_rejects_extra_signal_column_even_with_synced_checksum(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _assert_extra_column_rejected(valid_v4_5_frames, "signal")


def test_validator_v4_5_rejects_extra_order_column_even_with_synced_checksum(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _assert_extra_column_rejected(valid_v4_5_frames, "order")


def test_validator_v4_5_rejects_column_order_mismatch_even_with_synced_checksum(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset = valid_v4_5_frames["1m"]
    columns = list(dataset.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors = _validate_dataset_schema(dataset[columns], "1m")
    assert _errors_contain(errors, "V4.5 dataset schema mismatch")


def test_validator_v4_5_rejects_wrong_source_features_sha256_even_with_synced_checksum(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, labels, dataset = valid_v4_5_frames["5m"]
    dataset["source_features_sha256"] = "bad"
    errors = _source_value_errors("5m", features, labels, dataset)
    assert _errors_contain(errors, "V4.5 dataset physical mismatch")


def test_validator_v4_5_rejects_wrong_source_labels_sha256_even_with_synced_checksum(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, labels, dataset = valid_v4_5_frames["15m"]
    dataset["source_labels_sha256"] = "bad"
    errors = _source_value_errors("15m", features, labels, dataset)
    assert _errors_contain(errors, "V4.5 dataset physical mismatch")


def test_validator_v4_5_rejects_modified_feature_value_even_with_synced_checksum(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, labels, dataset = valid_v4_5_frames["1m"]
    dataset.loc[40, "return_1"] = float(dataset.loc[40, "return_1"]) + 1.0
    errors = _source_value_errors("1m", features, labels, dataset)
    assert _errors_contain(errors, "V4.5 dataset physical mismatch")


def test_validator_v4_5_rejects_modified_label_value_even_with_synced_checksum(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    features, labels, dataset = valid_v4_5_frames["1m"]
    dataset.loc[40, "future_log_return_h3"] = float(dataset.loc[40, "future_log_return_h3"]) + 1.0
    errors = _source_value_errors("1m", features, labels, dataset)
    assert _errors_contain(errors, "V4.5 dataset physical mismatch")


def test_validator_v4_5_rejects_feature_available_ts_after_decision_ts(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset = valid_v4_5_frames["1m"]
    dataset.loc[0, "feature_available_ts"] = pd.Timestamp(dataset.loc[0, "decision_ts"]) + pd.Timedelta(minutes=1)
    errors = _validate_dataset_temporal_rules(dataset, "1m")
    assert _errors_contain(errors, "feature_available_ts > decision_ts")


def test_validator_v4_5_rejects_label_available_ts_before_or_equal_decision_ts(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset = valid_v4_5_frames["1m"]
    dataset.loc[0, "label_available_ts"] = dataset.loc[0, "decision_ts"]
    errors = _validate_dataset_temporal_rules(dataset, "1m")
    assert _errors_contain(errors, "label_available_ts <= decision_ts")


def test_validator_v4_5_rejects_temporally_shuffled_split(
    valid_v4_5_frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]
) -> None:
    _features, _labels, dataset = valid_v4_5_frames["15m"]
    dataset.loc[0, "split"] = "test"
    dataset.loc[len(dataset) - 1, "split"] = "train"
    errors = _validate_dataset_temporal_rules(dataset, "15m")
    assert _errors_contain(errors, "split temporal order invalid")


def test_validator_v4_5_rejects_report_json_lie(valid_v4_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v4_5_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V4.5 quality report mismatch")


def test_validator_v4_5_rejects_manifest_unexpected_key(
    valid_v4_5_template: Path,
    valid_v4_5_manifest_report: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    manifest, _report = valid_v4_5_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(valid_v4_5_template, manifest)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v4_5_rejects_report_unexpected_key(valid_v4_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v4_5_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v4_5_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v4_5_template: Path) -> None:
    _copy_markdown_set(tmp_path, valid_v4_5_template)
    (tmp_path / REPORT_MD_PATH_V4_5).write_text(
        (tmp_path / REPORT_MD_PATH_V4_5).read_text(encoding="utf-8") + "\nStrategy validated.\n",
        encoding="utf-8",
    )
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v4_5_rejects_datacard_strategy_validated_claim(tmp_path: Path, valid_v4_5_template: Path) -> None:
    _copy_markdown_set(tmp_path, valid_v4_5_template)
    (tmp_path / DATACARD_MD_PATH_V4_5).write_text(
        (tmp_path / DATACARD_MD_PATH_V4_5).read_text(encoding="utf-8") + "\nStrategy validated.\n",
        encoding="utf-8",
    )
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v4_5_rejects_safety_flag_ml_true(valid_v4_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v4_5_manifest_report, "ml_enabled")


def test_validator_v4_5_rejects_safety_flag_backtest_true(valid_v4_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v4_5_manifest_report, "backtest_enabled")


def test_validator_v4_5_rejects_safety_flag_trading_true(valid_v4_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v4_5_manifest_report, "trading_enabled")


def test_validator_v4_5_rejects_safety_flag_orders_true(valid_v4_5_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v4_5_manifest_report, "orders_enabled")


def test_validator_v4_5_rejects_model_file_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "models/model.pkl")
    errors = _find_forbidden_v4_5_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V4.5")


def test_validator_v4_5_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v4_5_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V4.5")


def test_validator_v4_5_allows_dataset_outputs_only_in_v4_5_paths(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v4_5/datasets/offline_supervised/dummy.txt")
    assert _find_forbidden_v4_5_artifacts(tmp_path) == []


def _assert_extra_column_rejected(frames: dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]], column: str) -> None:
    _features, _labels, dataset = frames["1m"]
    dataset[column] = 0
    errors = _validate_dataset_schema(dataset, "1m")
    assert _errors_contain(errors, "V4.5 dataset schema mismatch")


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
    assert _errors_contain(errors, f"V4.5 safety flag {flag} must be False")


def _copy_markdown_set(target_root: Path, source_root: Path) -> None:
    for relative in [REPORT_MD_PATH_V4_5, DATACARD_MD_PATH_V4_5, Path("docs/one_year_offline_supervised_dataset_v4_5.md")]:
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
