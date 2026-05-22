from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.expanded_window import output_path as v3_5_ohlcv_path
from galapagos.data.public_market.storage import read_parquet
from galapagos.labels.expanded_window import (
    MANIFEST_PATH_V3_7,
    REPORT_JSON_PATH_V3_7,
    REPORT_MD_PATH_V3_7,
    TIMEFRAMES_V3_7,
    output_path,
)
from galapagos.labels.expanded_window_validation import (
    _find_forbidden_v3_7_artifacts,
    _validate_label_frame,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    validate_expanded_label_factory_v3_7,
)


@pytest.fixture(scope="session")
def valid_v3_7_template() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def valid_v3_7_validation_result(valid_v3_7_template: Path) -> dict[str, Any]:
    result = validate_expanded_label_factory_v3_7(valid_v3_7_template)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v3_7_manifest_report(valid_v3_7_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v3_7_template / MANIFEST_PATH_V3_7)), deepcopy(_load(valid_v3_7_template / REPORT_JSON_PATH_V3_7))


@pytest.fixture(scope="session")
def valid_v3_7_frame_cache(valid_v3_7_template: Path) -> dict[str, pd.DataFrame]:
    return {timeframe: read_parquet(output_path(valid_v3_7_template, timeframe)) for timeframe in TIMEFRAMES_V3_7}


@pytest.fixture()
def valid_v3_7_frames(valid_v3_7_frame_cache: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {timeframe: frame.copy(deep=True) for timeframe, frame in valid_v3_7_frame_cache.items()}


def test_validator_v3_7_accepts_valid_label_store(valid_v3_7_validation_result: dict[str, Any]) -> None:
    assert valid_v3_7_validation_result["passed"] is True
    assert valid_v3_7_validation_result["errors"] == []


def test_validator_v3_7_rejects_extra_signal_column_even_with_synced_checksum(
    valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]
) -> None:
    _assert_extra_column_rejected(valid_v3_7_template, valid_v3_7_frames, "signal")


def test_validator_v3_7_rejects_extra_strategy_column_even_with_synced_checksum(
    valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]
) -> None:
    _assert_extra_column_rejected(valid_v3_7_template, valid_v3_7_frames, "strategy")


def test_validator_v3_7_rejects_extra_order_column_even_with_synced_checksum(
    valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]
) -> None:
    _assert_extra_column_rejected(valid_v3_7_template, valid_v3_7_frames, "order")


def test_validator_v3_7_rejects_column_order_mismatch_even_with_synced_checksum(
    valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_7_frames["1m"]
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors, _quality = _frame_errors(valid_v3_7_template, "1m", frame[columns])
    assert _errors_contain(errors, "V3.7 label schema mismatch")


def test_validator_v3_7_rejects_wrong_source_ohlcv_sha256_even_with_synced_checksum(
    valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_7_frames["5m"]
    frame["source_ohlcv_sha256"] = "bad"
    errors, _quality = _frame_errors(valid_v3_7_template, "5m", frame)
    assert _errors_contain(errors, "V3.7 source_ohlcv_sha256 mismatch")


def test_validator_v3_7_rejects_label_available_ts_before_or_equal_decision_ts(
    valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_7_frames["1m"]
    frame.loc[0, "label_available_ts"] = frame.loc[0, "decision_ts"]
    errors, _quality = _frame_errors(valid_v3_7_template, "1m", frame)
    assert _errors_contain(errors, "label_available_ts <= decision_ts")


def test_validator_v3_7_rejects_wrong_future_close_h1(valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_7_frames["1m"]
    frame.loc[10, "future_close_h1"] = float(frame.loc[10, "future_close_h1"]) + 1.0
    errors, _quality = _frame_errors(valid_v3_7_template, "1m", frame)
    assert _errors_contain(errors, "future_close_h1 mismatch")


def test_validator_v3_7_rejects_wrong_future_log_return_h3(
    valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_7_frames["1m"]
    frame.loc[10, "future_log_return_h3"] = float(frame.loc[10, "future_log_return_h3"]) + 1.0
    errors, _quality = _frame_errors(valid_v3_7_template, "1m", frame)
    assert _errors_contain(errors, "future_log_return_h3 mismatch")


def test_validator_v3_7_rejects_wrong_direction_h5(valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_7_frames["5m"]
    frame.loc[10, "direction_h5"] = 99
    errors, _quality = _frame_errors(valid_v3_7_template, "5m", frame)
    assert _errors_contain(errors, "direction_h5 mismatch")


def test_validator_v3_7_rejects_wrong_up_down_flat_h1(
    valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]
) -> None:
    frame = valid_v3_7_frames["1h"]
    frame.loc[10, "up_down_flat_h1"] = "BROKEN"
    errors, _quality = _frame_errors(valid_v3_7_template, "1h", frame)
    assert _errors_contain(errors, "up_down_flat_h1 mismatch")


def test_validator_v3_7_rejects_wrong_label_valid_tail(valid_v3_7_template: Path, valid_v3_7_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_7_frames["15m"]
    frame.loc[len(frame) - 1, "label_valid_h1"] = True
    errors, _quality = _frame_errors(valid_v3_7_template, "15m", frame)
    assert _errors_contain(errors, "label_valid")


def test_validator_v3_7_rejects_report_json_lie(valid_v3_7_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v3_7_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V3.7 label report outputs mismatch")


def test_validator_v3_7_rejects_manifest_unexpected_key(
    valid_v3_7_template: Path,
    valid_v3_7_manifest_report: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    manifest, _report = valid_v3_7_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(valid_v3_7_template, manifest)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v3_7_rejects_report_unexpected_key(valid_v3_7_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v3_7_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v3_7_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v3_7_template: Path) -> None:
    path = tmp_path / REPORT_MD_PATH_V3_7
    path.parent.mkdir(parents=True, exist_ok=True)
    source_text = (valid_v3_7_template / REPORT_MD_PATH_V3_7).read_text(encoding="utf-8")
    path.write_text(source_text + "\nStrategy validated.\n", encoding="utf-8")
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v3_7_rejects_safety_flag_ml_true(valid_v3_7_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_7_manifest_report, "ml_enabled")


def test_validator_v3_7_rejects_safety_flag_dataset_true(valid_v3_7_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_7_manifest_report, "dataset_enabled")


def test_validator_v3_7_rejects_safety_flag_backtest_true(valid_v3_7_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_7_manifest_report, "backtest_enabled")


def test_validator_v3_7_rejects_safety_flag_trading_true(valid_v3_7_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_7_manifest_report, "trading_enabled")


def test_validator_v3_7_rejects_safety_flag_orders_true(valid_v3_7_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_7_manifest_report, "orders_enabled")


def test_validator_v3_7_rejects_dataset_ml_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v3_7/datasets/dummy.txt")
    errors = _find_forbidden_v3_7_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.7 artifact detected")


def test_validator_v3_7_rejects_ml_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v3_7/ml/dummy.txt")
    errors = _find_forbidden_v3_7_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.7 artifact detected")


def test_validator_v3_7_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v3_7_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.7 artifact detected")


def _assert_extra_column_rejected(root: Path, frames: dict[str, pd.DataFrame], column: str) -> None:
    frame = frames["1m"]
    frame[column] = 0
    errors, _quality = _frame_errors(root, "1m", frame)
    assert _errors_contain(errors, "V3.7 label schema mismatch")


def _frame_errors(root: Path, timeframe: str, frame: pd.DataFrame) -> tuple[list[str], dict[str, Any]]:
    input_path = v3_5_ohlcv_path(root, timeframe)
    input_frame = read_parquet(input_path)
    manifest = _load(root / MANIFEST_PATH_V3_7)
    return _validate_label_frame(timeframe, frame, input_path, input_frame, manifest["label_run_id"])


def _assert_safety_flag_rejected(manifest_report: tuple[dict[str, Any], dict[str, Any]], flag: str) -> None:
    manifest, _report = manifest_report
    manifest["safety"][flag] = True
    errors = _validate_safety(manifest["safety"])
    assert _errors_contain(errors, f"V3.7 safety flag {flag} must be False")


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("forbidden", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
