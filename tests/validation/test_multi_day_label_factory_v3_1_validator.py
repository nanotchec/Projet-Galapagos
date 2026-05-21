from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.multi_day import output_path as v2_9_ohlcv_path
from galapagos.data.public_market.storage import read_parquet
from galapagos.labels.multi_day import (
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    TIMEFRAMES_V3_1,
    output_path,
    run_multi_day_label_factory_v3_1,
)
from galapagos.labels.multi_day_validation import (
    _find_forbidden_v3_1_artifacts,
    _validate_label_frame,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    validate_multi_day_label_factory_v3_1,
)


@pytest.fixture(scope="session")
def valid_v3_1_template_data(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    root = tmp_path_factory.mktemp("valid_v3_1_validator")
    workspace = Path(__file__).resolve().parents[2]
    for timeframe in TIMEFRAMES_V3_1:
        source = v2_9_ohlcv_path(workspace, timeframe)
        destination = v2_9_ohlcv_path(root, timeframe)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    run_multi_day_label_factory_v3_1(root, validate_previous_layers=False)
    result = validate_multi_day_label_factory_v3_1(root)
    assert result["passed"], result["errors"]
    return root, result


@pytest.fixture(scope="session")
def valid_v3_1_template(valid_v3_1_template_data: tuple[Path, dict[str, Any]]) -> Path:
    root, _result = valid_v3_1_template_data
    return root


@pytest.fixture(scope="session")
def valid_v3_1_template_validation_result(valid_v3_1_template_data: tuple[Path, dict[str, Any]]) -> dict[str, Any]:
    _root, result = valid_v3_1_template_data
    return deepcopy(result)


@pytest.fixture()
def valid_v3_1_manifest_report(valid_v3_1_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v3_1_template / MANIFEST_PATH)), deepcopy(_load(valid_v3_1_template / REPORT_JSON_PATH))


@pytest.fixture(scope="session")
def valid_v3_1_frame_cache(valid_v3_1_template: Path) -> dict[str, pd.DataFrame]:
    return {timeframe: read_parquet(output_path(valid_v3_1_template, timeframe)) for timeframe in TIMEFRAMES_V3_1}


@pytest.fixture()
def valid_v3_1_frames(valid_v3_1_frame_cache: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {timeframe: frame.copy(deep=True) for timeframe, frame in valid_v3_1_frame_cache.items()}


def test_validator_v3_1_accepts_valid_label_store(valid_v3_1_template_validation_result: dict[str, Any]) -> None:
    result = valid_v3_1_template_validation_result
    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v3_1_rejects_extra_signal_column_even_with_synced_checksum(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    _assert_extra_column_rejected(valid_v3_1_template, valid_v3_1_frames, "signal")


def test_validator_v3_1_rejects_extra_strategy_column_even_with_synced_checksum(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    _assert_extra_column_rejected(valid_v3_1_template, valid_v3_1_frames, "strategy_validated")


def test_validator_v3_1_rejects_extra_order_column_even_with_synced_checksum(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    _assert_extra_column_rejected(valid_v3_1_template, valid_v3_1_frames, "order_side")


def test_validator_v3_1_rejects_column_order_mismatch_even_with_synced_checksum(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_1_frames["1m"]
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors, _quality = _frame_errors(valid_v3_1_template, "1m", frame[columns])
    assert _errors_contain(errors, "V3.1 label schema mismatch")


def test_validator_v3_1_rejects_wrong_source_ohlcv_sha256_even_with_synced_checksum(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_1_frames["5m"]
    frame["source_ohlcv_sha256"] = "bad"
    errors, _quality = _frame_errors(valid_v3_1_template, "5m", frame)
    assert _errors_contain(errors, "V3.1 source_ohlcv_sha256 mismatch")


def test_validator_v3_1_rejects_label_available_ts_before_or_equal_decision_ts(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_1_frames["1m"]
    frame.loc[0, "label_available_ts"] = frame.loc[0, "decision_ts"]
    errors, _quality = _frame_errors(valid_v3_1_template, "1m", frame)
    assert _errors_contain(errors, "label_available_ts <= decision_ts")


def test_validator_v3_1_rejects_wrong_future_close_h1(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_1_frames["1m"]
    frame.loc[0, "future_close_h1"] = float(frame.loc[0, "future_close_h1"]) + 1.0
    errors, _quality = _frame_errors(valid_v3_1_template, "1m", frame)
    assert _errors_contain(errors, "future_close_h1 mismatch")


def test_validator_v3_1_rejects_wrong_future_log_return_h3(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_1_frames["1m"]
    frame.loc[0, "future_log_return_h3"] = float(frame.loc[0, "future_log_return_h3"]) + 0.01
    errors, _quality = _frame_errors(valid_v3_1_template, "1m", frame)
    assert _errors_contain(errors, "future_log_return_h3 mismatch")


def test_validator_v3_1_rejects_wrong_direction_h5(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_1_frames["1m"]
    frame.loc[0, "direction_h5"] = 9.0
    errors, _quality = _frame_errors(valid_v3_1_template, "1m", frame)
    assert _errors_contain(errors, "direction_h5 mismatch")


def test_validator_v3_1_rejects_wrong_up_down_flat_h1(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_1_frames["1m"]
    frame.loc[0, "up_down_flat_h1"] = "BROKEN"
    errors, _quality = _frame_errors(valid_v3_1_template, "1m", frame)
    assert _errors_contain(errors, "up_down_flat_h1 mismatch")


def test_validator_v3_1_rejects_wrong_label_valid_tail(valid_v3_1_template: Path, valid_v3_1_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v3_1_frames["1m"]
    frame.loc[len(frame) - 1, "label_valid_h1"] = True
    errors, _quality = _frame_errors(valid_v3_1_template, "1m", frame)
    assert _errors_contain(errors, "label_valid")


def test_validator_v3_1_rejects_report_json_lie(valid_v3_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v3_1_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V3.1 label report outputs mismatch")


def test_validator_v3_1_rejects_manifest_unexpected_key(valid_v3_1_template: Path, valid_v3_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v3_1_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(valid_v3_1_template, manifest)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v3_1_rejects_report_unexpected_key(valid_v3_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v3_1_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v3_1_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v3_1_template: Path) -> None:
    path = tmp_path / REPORT_MD_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((valid_v3_1_template / REPORT_MD_PATH).read_text(encoding="utf-8") + "\nStrategy validated.\n", encoding="utf-8")
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v3_1_rejects_safety_flag_ml_true(valid_v3_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_1_manifest_report, "ml_enabled")


def test_validator_v3_1_rejects_safety_flag_dataset_true(valid_v3_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_1_manifest_report, "dataset_enabled")


def test_validator_v3_1_rejects_safety_flag_backtest_true(valid_v3_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_1_manifest_report, "backtest_enabled")


def test_validator_v3_1_rejects_safety_flag_trading_true(valid_v3_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_1_manifest_report, "trading_enabled")


def test_validator_v3_1_rejects_safety_flag_orders_true(valid_v3_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v3_1_manifest_report, "orders_enabled")


def test_validator_v3_1_rejects_dataset_ml_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v3_1/datasets/dummy.txt")
    errors = _find_forbidden_v3_1_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.1 artifact detected")


def test_validator_v3_1_rejects_ml_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v3_1/ml/dummy.txt")
    errors = _find_forbidden_v3_1_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.1 artifact detected")


def test_validator_v3_1_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v3_1_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V3.1 artifact detected")


def _assert_extra_column_rejected(root: Path, frames: dict[str, pd.DataFrame], column: str) -> None:
    frame = frames["1m"]
    frame[column] = 0
    errors, _quality = _frame_errors(root, "1m", frame)
    assert _errors_contain(errors, "V3.1 label schema mismatch")


def _frame_errors(root: Path, timeframe: str, frame: pd.DataFrame) -> tuple[list[str], dict[str, Any]]:
    input_path = v2_9_ohlcv_path(root, timeframe)
    input_frame = read_parquet(input_path)
    manifest = _load(root / MANIFEST_PATH)
    return _validate_label_frame(timeframe, frame, input_path, input_frame, manifest["label_run_id"])


def _assert_safety_flag_rejected(manifest_report: tuple[dict[str, Any], dict[str, Any]], flag: str) -> None:
    manifest, _report = manifest_report
    manifest["safety"][flag] = True
    errors = _validate_safety(manifest["safety"])
    assert _errors_contain(errors, f"V3.1 safety flag {flag} must be False")


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("forbidden", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
