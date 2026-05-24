from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.max_history_window import MANIFEST_PATH_V5_0, REPORT_JSON_PATH_V5_0, REPORT_MD_PATH_V5_0, output_path
from galapagos.data.public_market.max_history_window_quality import parent_child_consistent
from galapagos.data.public_market.max_history_window_validation import (
    _find_forbidden_v5_0_artifacts,
    _validate_markdown,
    _validate_ohlcv_frame,
    _validate_output_entry,
    _validate_raw_files,
    _validate_report,
    _validate_safety,
    validate_max_history_public_market_data_v5_0,
)
from galapagos.data.public_market.storage import read_parquet


@pytest.fixture(scope="session")
def valid_v5_0_template() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def valid_v5_0_manifest(valid_v5_0_template: Path) -> dict[str, Any]:
    return json.loads((valid_v5_0_template / MANIFEST_PATH_V5_0).read_text(encoding="utf-8"))


@pytest.fixture()
def valid_v5_0_manifest_report(valid_v5_0_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        deepcopy(json.loads((valid_v5_0_template / MANIFEST_PATH_V5_0).read_text(encoding="utf-8"))),
        deepcopy(json.loads((valid_v5_0_template / REPORT_JSON_PATH_V5_0).read_text(encoding="utf-8"))),
    )


@pytest.fixture(scope="session")
def valid_v5_0_frame_cache(valid_v5_0_template: Path) -> dict[str, pd.DataFrame]:
    return {timeframe: read_parquet(output_path(valid_v5_0_template, timeframe)) for timeframe in ["1m", "5m", "15m", "1h"]}


@pytest.fixture()
def valid_v5_0_frames(valid_v5_0_frame_cache: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {timeframe: frame.copy(deep=True) for timeframe, frame in valid_v5_0_frame_cache.items()}


def test_validator_v5_0_accepts_valid_max_history_data(valid_v5_0_template: Path) -> None:
    result = validate_max_history_public_market_data_v5_0(valid_v5_0_template)
    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v5_0_rejects_missing_raw_zip(tmp_path: Path, valid_v5_0_manifest: dict[str, Any]) -> None:
    errors, _raw_rows = _validate_raw_files(tmp_path, valid_v5_0_manifest)
    assert _errors_contain(errors, "missing raw zip")


def test_validator_v5_0_rejects_wrong_raw_checksum(valid_v5_0_template: Path, valid_v5_0_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v5_0_manifest_report
    first_date = sorted(manifest["raw_files"])[0]
    manifest["raw_files"][first_date]["sha256"] = "bad"
    errors, _raw_rows = _validate_raw_files(valid_v5_0_template, manifest)
    assert _errors_contain(errors, "V5.0 raw sha256 mismatch")


def test_validator_v5_0_rejects_deleted_1m_row_even_with_synced_checksum(valid_v5_0_frames: dict[str, pd.DataFrame], valid_v5_0_manifest: dict[str, Any]) -> None:
    frame = valid_v5_0_frames["1m"].iloc[:-1].reset_index(drop=True)
    errors = _validate_ohlcv_frame("1m", frame, valid_v5_0_manifest)
    assert _errors_contain(errors, "V5.0 physical quality error for 1m")


def test_validator_v5_0_rejects_duplicate_1m_row_even_with_synced_checksum(valid_v5_0_frames: dict[str, pd.DataFrame], valid_v5_0_manifest: dict[str, Any]) -> None:
    frame = valid_v5_0_frames["1m"]
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    errors = _validate_ohlcv_frame("1m", frame, valid_v5_0_manifest)
    assert _errors_contain(errors, "duplicate")


def test_validator_v5_0_rejects_shuffled_1m_parquet_even_with_synced_checksum(valid_v5_0_frames: dict[str, pd.DataFrame], valid_v5_0_manifest: dict[str, Any]) -> None:
    frame = valid_v5_0_frames["1m"].sample(frac=1.0, random_state=42).reset_index(drop=True)
    errors = _validate_ohlcv_frame("1m", frame, valid_v5_0_manifest)
    assert _errors_contain(errors, "monotonic")


def test_validator_v5_0_rejects_extra_future_return_column_even_with_synced_checksum(valid_v5_0_frames: dict[str, pd.DataFrame], valid_v5_0_manifest: dict[str, Any]) -> None:
    frame = valid_v5_0_frames["1m"]
    frame["future_return"] = 0.0
    errors = _validate_ohlcv_frame("1m", frame, valid_v5_0_manifest)
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v5_0_rejects_extra_signal_column_even_with_synced_checksum(valid_v5_0_frames: dict[str, pd.DataFrame], valid_v5_0_manifest: dict[str, Any]) -> None:
    frame = valid_v5_0_frames["1m"]
    frame["signal"] = 0
    errors = _validate_ohlcv_frame("1m", frame, valid_v5_0_manifest)
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v5_0_rejects_column_order_mismatch_even_with_synced_checksum(valid_v5_0_frames: dict[str, pd.DataFrame], valid_v5_0_manifest: dict[str, Any]) -> None:
    frame = valid_v5_0_frames["1m"]
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors = _validate_ohlcv_frame("1m", frame[columns], valid_v5_0_manifest)
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v5_0_rejects_modified_5m_high_even_with_synced_checksum(valid_v5_0_frames: dict[str, pd.DataFrame]) -> None:
    frame_1m = valid_v5_0_frames["1m"]
    frame = valid_v5_0_frames["5m"]
    frame.loc[0, "high"] = float(frame.loc[0, "high"]) + 100.0
    assert not parent_child_consistent(frame_1m, frame, "5m")


def test_validator_v5_0_rejects_manifest_output_rows_lie(
    valid_v5_0_template: Path,
    valid_v5_0_manifest_report: tuple[dict[str, Any], dict[str, Any]],
    valid_v5_0_frames: dict[str, pd.DataFrame],
) -> None:
    manifest, _report = valid_v5_0_manifest_report
    manifest["outputs"]["5m"]["rows"] = 123
    errors = _validate_output_entry(valid_v5_0_template, manifest, "5m", output_path(valid_v5_0_template, "5m"), valid_v5_0_frames["5m"])
    assert _errors_contain(errors, "V5.0 manifest output mismatch for 5m.rows")


def test_validator_v5_0_rejects_report_output_sha_lie(valid_v5_0_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v5_0_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V5.0 quality report mismatch")


def test_validator_v5_0_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v5_0_template: Path) -> None:
    path = tmp_path / REPORT_MD_PATH_V5_0
    path.parent.mkdir(parents=True, exist_ok=True)
    source_text = (valid_v5_0_template / REPORT_MD_PATH_V5_0).read_text(encoding="utf-8")
    path.write_text(source_text + "\nStrategy validated.\n", encoding="utf-8")
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "V5.0 Markdown report")


def test_validator_v5_0_rejects_safety_flag_trading_true(valid_v5_0_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v5_0_manifest_report
    manifest["safety"]["trading_enabled"] = True
    errors = _validate_safety(manifest["safety"])
    assert _errors_contain(errors, "V5.0 safety flag trading_enabled must be False")


def test_validator_v5_0_rejects_features_v5_0_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v5_0/features/dummy.txt")
    errors = _find_forbidden_v5_0_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.0 artifact detected")


def test_validator_v5_0_rejects_labels_v5_0_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v5_0/labels/dummy.txt")
    errors = _find_forbidden_v5_0_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.0 artifact detected")


def test_validator_v5_0_rejects_dataset_ml_v5_0_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v5_0/datasets/ml/dummy.txt")
    errors = _find_forbidden_v5_0_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.0 artifact detected")


def test_validator_v5_0_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v5_0_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.0 artifact detected")


def test_validator_v5_0_raw_to_1m_validation_is_vectorized(valid_v5_0_template: Path) -> None:
    source = valid_v5_0_template / "src/galapagos/data/public_market/max_history_window_validation.py"
    function_source = _extract_function_source(source.read_text(encoding="utf-8"), "_validate_raw_to_1m")
    assert '.dt.strftime("%Y-%m-%d") == current_date' not in function_source
    assert 'groupby("_date"' in function_source


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("forbidden", encoding="utf-8")


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)


def _extract_function_source(source: str, function_name: str) -> str:
    start = source.index(f"def {function_name}")
    next_function = source.find("\ndef ", start + 1)
    if next_function == -1:
        return source[start:]
    return source[start:next_function]
