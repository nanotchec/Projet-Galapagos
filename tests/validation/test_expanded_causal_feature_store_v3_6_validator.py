from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.expanded_window import output_path as v3_5_ohlcv_path
from galapagos.data.public_market.storage import read_parquet
from galapagos.features.expanded_window import (
    MANIFEST_PATH_V3_6,
    REPORT_JSON_PATH_V3_6,
    REPORT_MD_PATH_V3_6,
    TIMEFRAMES_V3_6,
    output_path,
)
from galapagos.features.expanded_window_validation import (
    _find_forbidden_v3_6_artifacts,
    _validate_feature_frame,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    validate_expanded_causal_feature_store_v3_6,
)


@pytest.fixture(scope="session")
def valid_v3_6_template() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def valid_v3_6_validation_result(valid_v3_6_template: Path) -> dict[str, Any]:
    result = validate_expanded_causal_feature_store_v3_6(valid_v3_6_template)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v3_6_manifest_report(valid_v3_6_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v3_6_template / MANIFEST_PATH_V3_6)), deepcopy(_load(valid_v3_6_template / REPORT_JSON_PATH_V3_6))


@pytest.fixture(scope="session")
def valid_v3_6_frame_cache(valid_v3_6_template: Path) -> dict[str, pd.DataFrame]:
    return {timeframe: read_parquet(output_path(valid_v3_6_template, timeframe)) for timeframe in TIMEFRAMES_V3_6}


@pytest.fixture()
def valid_v3_6_frames(valid_v3_6_frame_cache: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {timeframe: frame.copy(deep=True) for timeframe, frame in valid_v3_6_frame_cache.items()}


def test_validator_v3_6_accepts_valid_feature_store(valid_v3_6_validation_result: dict[str, Any]) -> None:
    assert valid_v3_6_validation_result["passed"] is True
    assert valid_v3_6_validation_result["errors"] == []


def test_validator_v3_6_rejects_extra_future_return_column_even_with_synced_checksum(
    valid_v3_6_template: Path, valid_v3_6_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_6_frames["1m"]
    frame["future_return"] = 0.0
    errors, _quality = _frame_errors(valid_v3_6_template, "1m", frame)
    assert _errors_contain(errors, "V3.6 feature schema mismatch")


def test_validator_v3_6_rejects_extra_label_column_even_with_synced_checksum(
    valid_v3_6_template: Path, valid_v3_6_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_6_frames["1m"]
    frame["label_direction"] = 0
    errors, _quality = _frame_errors(valid_v3_6_template, "1m", frame)
    assert _errors_contain(errors, "V3.6 feature schema mismatch")


def test_validator_v3_6_rejects_extra_signal_column_even_with_synced_checksum(
    valid_v3_6_template: Path, valid_v3_6_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_6_frames["1m"]
    frame["signal"] = 0
    errors, _quality = _frame_errors(valid_v3_6_template, "1m", frame)
    assert _errors_contain(errors, "V3.6 feature schema mismatch")


def test_validator_v3_6_rejects_extra_prediction_column_even_with_synced_checksum(
    valid_v3_6_template: Path, valid_v3_6_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_6_frames["1m"]
    frame["prediction"] = 0
    errors, _quality = _frame_errors(valid_v3_6_template, "1m", frame)
    assert _errors_contain(errors, "V3.6 feature schema mismatch")


def test_validator_v3_6_rejects_column_order_mismatch_even_with_synced_checksum(
    valid_v3_6_template: Path, valid_v3_6_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_6_frames["1m"]
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors, _quality = _frame_errors(valid_v3_6_template, "1m", frame[columns])
    assert _errors_contain(errors, "V3.6 feature schema mismatch")


def test_validator_v3_6_rejects_wrong_source_ohlcv_sha256_even_with_synced_checksum(
    valid_v3_6_template: Path, valid_v3_6_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_6_frames["5m"]
    frame["source_ohlcv_sha256"] = "bad"
    errors, _quality = _frame_errors(valid_v3_6_template, "5m", frame)
    assert _errors_contain(errors, "V3.6 source_ohlcv_sha256 mismatch")


def test_validator_v3_6_rejects_feature_available_ts_before_available_ts(
    valid_v3_6_template: Path, valid_v3_6_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_6_frames["1m"]
    frame.loc[0, "feature_available_ts"] = pd.Timestamp("2023-12-31T23:59:00Z")
    errors, _quality = _frame_errors(valid_v3_6_template, "1m", frame)
    assert _errors_contain(errors, "feature_available_ts < available_ts")


def test_validator_v3_6_rejects_decision_ts_before_feature_available_ts(
    valid_v3_6_template: Path, valid_v3_6_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_6_frames["1m"]
    frame.loc[0, "decision_ts"] = pd.Timestamp("2023-12-31T23:59:00Z")
    errors, _quality = _frame_errors(valid_v3_6_template, "1m", frame)
    assert _errors_contain(errors, "decision_ts < feature_available_ts")


def test_validator_v3_6_rejects_report_json_lie(valid_v3_6_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v3_6_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V3.6 feature report outputs mismatch")


def test_validator_v3_6_rejects_manifest_unexpected_key(
    valid_v3_6_template: Path,
    valid_v3_6_manifest_report: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    manifest, _report = valid_v3_6_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(valid_v3_6_template, manifest)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v3_6_rejects_report_unexpected_key(valid_v3_6_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v3_6_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v3_6_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v3_6_template: Path) -> None:
    path = tmp_path / REPORT_MD_PATH_V3_6
    path.parent.mkdir(parents=True, exist_ok=True)
    source_text = (valid_v3_6_template / REPORT_MD_PATH_V3_6).read_text(encoding="utf-8")
    path.write_text(source_text + "\nStrategy validated.\n", encoding="utf-8")
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v3_6_rejects_safety_flag_ml_true(valid_v3_6_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_6_manifest_report, "ml_enabled")


def test_validator_v3_6_rejects_safety_flag_labels_true(valid_v3_6_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_6_manifest_report, "labels_enabled")


def test_validator_v3_6_rejects_safety_flag_dataset_true(valid_v3_6_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_6_manifest_report, "dataset_enabled")


def test_validator_v3_6_rejects_safety_flag_backtest_true(valid_v3_6_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_6_manifest_report, "backtest_enabled")


def test_validator_v3_6_rejects_safety_flag_trading_true(valid_v3_6_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_6_manifest_report, "trading_enabled")


def test_validator_v3_6_rejects_labels_v3_6_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v3_6/labels/dummy.txt")
    errors = _find_forbidden_v3_6_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.6 artifact detected")


def test_validator_v3_6_rejects_datasets_v3_6_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v3_6/datasets/dummy.txt")
    errors = _find_forbidden_v3_6_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.6 artifact detected")


def test_validator_v3_6_rejects_ml_v3_6_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v3_6/ml/dummy.txt")
    errors = _find_forbidden_v3_6_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.6 artifact detected")


def test_validator_v3_6_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v3_6_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.6 artifact detected")


def _frame_errors(root: Path, timeframe: str, frame: pd.DataFrame) -> tuple[list[str], dict[str, Any]]:
    input_path = v3_5_ohlcv_path(root, timeframe)
    input_frame = read_parquet(input_path)
    manifest = _load(root / MANIFEST_PATH_V3_6)
    return _validate_feature_frame(timeframe, frame, input_path, input_frame, manifest["feature_run_id"])


def _assert_safety_flag_rejected(manifest_report: tuple[dict[str, Any], dict[str, Any]], flag: str) -> None:
    manifest, _report = manifest_report
    manifest["safety"][flag] = True
    errors = _validate_safety(manifest["safety"])
    assert _errors_contain(errors, f"V3.6 safety flag {flag} must be False")


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("forbidden", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
