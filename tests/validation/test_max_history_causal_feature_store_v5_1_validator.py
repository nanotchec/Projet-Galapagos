from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.storage import read_parquet
from galapagos.features.max_history_window import (
    MANIFEST_PATH_V5_1,
    REPORT_JSON_PATH_V5_1,
    REPORT_MD_PATH_V5_1,
    input_ohlcv_path,
    load_v5_0_ohlcv_manifest,
    output_path,
)
from galapagos.features.max_history_window_validation import (
    _find_forbidden_v5_1_artifacts,
    _validate_feature_frame,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    validate_max_history_causal_feature_store_v5_1,
)


@pytest.fixture(scope="session")
def valid_v5_1_template() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def v5_0_manifest(valid_v5_1_template: Path) -> dict[str, Any]:
    return load_v5_0_ohlcv_manifest(valid_v5_1_template)


@pytest.fixture(scope="session")
def valid_v5_1_validation_result(valid_v5_1_template: Path) -> dict[str, Any]:
    result = validate_max_history_causal_feature_store_v5_1(valid_v5_1_template)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v5_1_manifest_report(valid_v5_1_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v5_1_template / MANIFEST_PATH_V5_1)), deepcopy(
        _load(valid_v5_1_template / REPORT_JSON_PATH_V5_1)
    )


@pytest.fixture(scope="session")
def valid_v5_1_frame_cache(valid_v5_1_template: Path, v5_0_manifest: dict[str, Any]) -> dict[str, pd.DataFrame]:
    window_start = v5_0_manifest["discovery"]["window_start"]
    window_end = v5_0_manifest["discovery"]["window_end"]
    return {
        timeframe: read_parquet(output_path(valid_v5_1_template, timeframe, window_start, window_end))
        for timeframe in ["1h", "5m"]
    }


@pytest.fixture()
def valid_v5_1_frames(valid_v5_1_frame_cache: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {timeframe: frame.copy(deep=True) for timeframe, frame in valid_v5_1_frame_cache.items()}


def test_validator_v5_1_accepts_valid_feature_store(valid_v5_1_validation_result: dict[str, Any]) -> None:
    assert valid_v5_1_validation_result["passed"] is True
    assert valid_v5_1_validation_result["errors"] == []


def test_validator_v5_1_rejects_extra_future_return_column_even_with_synced_checksum(
    valid_v5_1_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_1_frames["1h"]
    frame["future_return"] = 0.0
    errors, _quality = _frame_errors(valid_v5_1_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "V5.1 feature schema mismatch")


def test_validator_v5_1_rejects_extra_label_column_even_with_synced_checksum(
    valid_v5_1_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_1_frames["1h"]
    frame["label_direction"] = 0
    errors, _quality = _frame_errors(valid_v5_1_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "V5.1 feature schema mismatch")


def test_validator_v5_1_rejects_extra_signal_column_even_with_synced_checksum(
    valid_v5_1_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_1_frames["1h"]
    frame["signal"] = 0
    errors, _quality = _frame_errors(valid_v5_1_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "V5.1 feature schema mismatch")


def test_validator_v5_1_rejects_extra_prediction_column_even_with_synced_checksum(
    valid_v5_1_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_1_frames["1h"]
    frame["prediction"] = 0
    errors, _quality = _frame_errors(valid_v5_1_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "V5.1 feature schema mismatch")


def test_validator_v5_1_rejects_column_order_mismatch_even_with_synced_checksum(
    valid_v5_1_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_1_frames["1h"]
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors, _quality = _frame_errors(valid_v5_1_template, v5_0_manifest, "1h", frame[columns])
    assert _errors_contain(errors, "V5.1 feature schema mismatch")


def test_validator_v5_1_rejects_wrong_source_ohlcv_sha256_even_with_synced_checksum(
    valid_v5_1_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_1_frames["5m"]
    frame["source_ohlcv_sha256"] = "bad"
    errors, _quality = _frame_errors(valid_v5_1_template, v5_0_manifest, "5m", frame)
    assert _errors_contain(errors, "V5.1 source_ohlcv_sha256 mismatch")


def test_validator_v5_1_rejects_feature_available_ts_before_available_ts(
    valid_v5_1_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_1_frames["1h"]
    frame.loc[0, "feature_available_ts"] = pd.Timestamp("2023-03-24T23:59:00Z")
    errors, _quality = _frame_errors(valid_v5_1_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "feature_available_ts < available_ts")


def test_validator_v5_1_rejects_decision_ts_before_feature_available_ts(
    valid_v5_1_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_1_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_1_frames["1h"]
    frame.loc[0, "decision_ts"] = pd.Timestamp("2023-03-24T23:59:00Z")
    errors, _quality = _frame_errors(valid_v5_1_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "decision_ts < feature_available_ts")


def test_validator_v5_1_rejects_report_json_lie(valid_v5_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v5_1_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V5.1 feature report outputs mismatch")


def test_validator_v5_1_rejects_manifest_unexpected_key(
    valid_v5_1_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_1_manifest_report: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    manifest, _report = valid_v5_1_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(valid_v5_1_template, manifest, v5_0_manifest)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v5_1_rejects_report_unexpected_key(valid_v5_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v5_1_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v5_1_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v5_1_template: Path) -> None:
    path = tmp_path / REPORT_MD_PATH_V5_1
    path.parent.mkdir(parents=True, exist_ok=True)
    source_text = (valid_v5_1_template / REPORT_MD_PATH_V5_1).read_text(encoding="utf-8")
    path.write_text(source_text + "\nStrategy validated.\n", encoding="utf-8")
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v5_1_rejects_safety_flag_ml_true(valid_v5_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_1_manifest_report, "ml_enabled")


def test_validator_v5_1_rejects_safety_flag_labels_true(valid_v5_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_1_manifest_report, "labels_enabled")


def test_validator_v5_1_rejects_safety_flag_dataset_true(valid_v5_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_1_manifest_report, "dataset_enabled")


def test_validator_v5_1_rejects_safety_flag_backtest_true(valid_v5_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_1_manifest_report, "backtest_enabled")


def test_validator_v5_1_rejects_safety_flag_trading_true(valid_v5_1_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_1_manifest_report, "trading_enabled")


def test_validator_v5_1_rejects_labels_v5_1_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v5_1/labels/dummy.txt")
    errors = _find_forbidden_v5_1_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.1 artifact detected")


def test_validator_v5_1_rejects_datasets_v5_1_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v5_1/datasets/dummy.txt")
    errors = _find_forbidden_v5_1_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.1 artifact detected")


def test_validator_v5_1_rejects_ml_v5_1_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v5_1/ml/dummy.txt")
    errors = _find_forbidden_v5_1_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.1 artifact detected")


def test_validator_v5_1_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v5_1_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.1 artifact detected")


def _frame_errors(
    root: Path,
    v5_0_manifest: dict[str, Any],
    timeframe: str,
    frame: pd.DataFrame,
) -> tuple[list[str], dict[str, Any]]:
    input_path = input_ohlcv_path(root, timeframe, v5_0_manifest)
    input_frame = read_parquet(input_path)
    manifest = _load(root / MANIFEST_PATH_V5_1)
    return _validate_feature_frame(
        timeframe,
        frame,
        input_path,
        input_frame,
        manifest["feature_run_id"],
        expected_rows=int(v5_0_manifest["expected_rows"][timeframe]),
    )


def _assert_safety_flag_rejected(manifest_report: tuple[dict[str, Any], dict[str, Any]], flag: str) -> None:
    manifest, _report = manifest_report
    manifest["safety"][flag] = True
    errors = _validate_safety(manifest["safety"])
    assert _errors_contain(errors, f"V5.1 safety flag {flag} must be False")


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("forbidden", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
