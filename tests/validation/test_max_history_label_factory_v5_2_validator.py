from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet
from galapagos.labels.forward_returns import build_forward_labels
from galapagos.labels.max_history_window import (
    LABEL_SCHEMA_VERSION_V5_2,
    MANIFEST_PATH_V5_2,
    REPORT_JSON_PATH_V5_2,
    REPORT_MD_PATH_V5_2,
    input_ohlcv_path,
    load_v5_0_ohlcv_manifest,
)
from galapagos.labels.max_history_window_validation import (
    _find_forbidden_v5_2_artifacts,
    _validate_label_frame,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    validate_max_history_label_factory_v5_2,
)


@pytest.fixture(scope="session")
def valid_v5_2_template() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def v5_0_manifest(valid_v5_2_template: Path) -> dict[str, Any]:
    return load_v5_0_ohlcv_manifest(valid_v5_2_template)


@pytest.fixture(scope="session")
def valid_v5_2_validation_result(valid_v5_2_template: Path) -> dict[str, Any]:
    result = validate_max_history_label_factory_v5_2(valid_v5_2_template)
    assert result["passed"], result["errors"]
    return deepcopy(result)


@pytest.fixture()
def valid_v5_2_manifest_report(valid_v5_2_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v5_2_template / MANIFEST_PATH_V5_2)), deepcopy(
        _load(valid_v5_2_template / REPORT_JSON_PATH_V5_2)
    )


@pytest.fixture(scope="session")
def valid_v5_2_frame_cache(valid_v5_2_template: Path, v5_0_manifest: dict[str, Any]) -> dict[str, pd.DataFrame]:
    manifest = _load(valid_v5_2_template / MANIFEST_PATH_V5_2)
    frames: dict[str, pd.DataFrame] = {}
    for timeframe in ["1h", "5m"]:
        input_path = input_ohlcv_path(valid_v5_2_template, timeframe, v5_0_manifest)
        input_frame = read_parquet(input_path).head(2000).reset_index(drop=True)
        frames[timeframe] = build_forward_labels(
            input_frame,
            sha256_file(input_path),
            manifest["label_run_id"],
            label_schema_version=LABEL_SCHEMA_VERSION_V5_2,
        )
    return frames


@pytest.fixture()
def valid_v5_2_frames(valid_v5_2_frame_cache: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {timeframe: frame.copy(deep=True) for timeframe, frame in valid_v5_2_frame_cache.items()}


def test_validator_v5_2_accepts_valid_label_store(valid_v5_2_validation_result: dict[str, Any]) -> None:
    assert valid_v5_2_validation_result["passed"] is True
    assert valid_v5_2_validation_result["errors"] == []


def test_validator_v5_2_rejects_extra_signal_column_even_with_synced_checksum(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    _assert_extra_column_rejected(valid_v5_2_template, v5_0_manifest, valid_v5_2_frames, "signal")


def test_validator_v5_2_rejects_extra_strategy_column_even_with_synced_checksum(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    _assert_extra_column_rejected(valid_v5_2_template, v5_0_manifest, valid_v5_2_frames, "strategy")


def test_validator_v5_2_rejects_extra_order_column_even_with_synced_checksum(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    _assert_extra_column_rejected(valid_v5_2_template, v5_0_manifest, valid_v5_2_frames, "order")


def test_validator_v5_2_rejects_column_order_mismatch_even_with_synced_checksum(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_2_frames["1h"]
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors, _quality = _frame_errors(valid_v5_2_template, v5_0_manifest, "1h", frame[columns])
    assert _errors_contain(errors, "V5.2 label schema mismatch")


def test_validator_v5_2_rejects_wrong_source_ohlcv_sha256_even_with_synced_checksum(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_2_frames["5m"]
    frame["source_ohlcv_sha256"] = "bad"
    errors, _quality = _frame_errors(valid_v5_2_template, v5_0_manifest, "5m", frame)
    assert _errors_contain(errors, "V5.2 source_ohlcv_sha256 mismatch")


def test_validator_v5_2_rejects_label_available_ts_before_or_equal_decision_ts(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_2_frames["1h"]
    frame.loc[0, "label_available_ts"] = frame.loc[0, "decision_ts"]
    errors, _quality = _frame_errors(valid_v5_2_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "label_available_ts <= decision_ts")


def test_validator_v5_2_rejects_wrong_future_close_h1(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_2_frames["1h"]
    frame.loc[10, "future_close_h1"] = float(frame.loc[10, "future_close_h1"]) + 1.0
    errors, _quality = _frame_errors(valid_v5_2_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "future_close_h1 mismatch")


def test_validator_v5_2_rejects_wrong_future_log_return_h3(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_2_frames["1h"]
    frame.loc[10, "future_log_return_h3"] = float(frame.loc[10, "future_log_return_h3"]) + 1.0
    errors, _quality = _frame_errors(valid_v5_2_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "future_log_return_h3 mismatch")


def test_validator_v5_2_rejects_wrong_direction_h5(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_2_frames["5m"]
    frame.loc[10, "direction_h5"] = 99
    errors, _quality = _frame_errors(valid_v5_2_template, v5_0_manifest, "5m", frame)
    assert _errors_contain(errors, "direction_h5 mismatch")


def test_validator_v5_2_rejects_wrong_up_down_flat_h1(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_2_frames["1h"]
    frame.loc[10, "up_down_flat_h1"] = "BROKEN"
    errors, _quality = _frame_errors(valid_v5_2_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "up_down_flat_h1 mismatch")


def test_validator_v5_2_rejects_wrong_label_valid_tail(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_frames: dict[str, pd.DataFrame],
) -> None:
    frame = valid_v5_2_frames["1h"]
    frame.loc[len(frame) - 1, "label_valid_h1"] = True
    errors, _quality = _frame_errors(valid_v5_2_template, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "label_valid")


def test_validator_v5_2_rejects_report_json_lie(valid_v5_2_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v5_2_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V5.2 label report outputs mismatch")


def test_validator_v5_2_rejects_manifest_unexpected_key(
    valid_v5_2_template: Path,
    v5_0_manifest: dict[str, Any],
    valid_v5_2_manifest_report: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    manifest, _report = valid_v5_2_manifest_report
    manifest["strategy_validated"] = True
    errors = _validate_manifest_structure(valid_v5_2_template, manifest, v5_0_manifest)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v5_2_rejects_report_unexpected_key(valid_v5_2_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v5_2_manifest_report
    report["claim"] = "strategy validated"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v5_2_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v5_2_template: Path) -> None:
    path = tmp_path / REPORT_MD_PATH_V5_2
    path.parent.mkdir(parents=True, exist_ok=True)
    source_text = (valid_v5_2_template / REPORT_MD_PATH_V5_2).read_text(encoding="utf-8")
    path.write_text(source_text + "\nStrategy validated.\n", encoding="utf-8")
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "forbidden claim")


def test_validator_v5_2_rejects_safety_flag_ml_true(valid_v5_2_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_2_manifest_report, "ml_enabled")


def test_validator_v5_2_rejects_safety_flag_dataset_true(valid_v5_2_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_2_manifest_report, "dataset_enabled")


def test_validator_v5_2_rejects_safety_flag_backtest_true(valid_v5_2_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_2_manifest_report, "backtest_enabled")


def test_validator_v5_2_rejects_safety_flag_trading_true(valid_v5_2_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_2_manifest_report, "trading_enabled")


def test_validator_v5_2_rejects_safety_flag_orders_true(valid_v5_2_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    _assert_safety_flag_rejected(valid_v5_2_manifest_report, "orders_enabled")


def test_validator_v5_2_rejects_dataset_ml_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v5_2/datasets/dummy.txt")
    errors = _find_forbidden_v5_2_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.2 artifact detected")


def test_validator_v5_2_rejects_ml_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v5_2/ml/dummy.txt")
    errors = _find_forbidden_v5_2_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.2 artifact detected")


def test_validator_v5_2_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v5_2_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V5.2 artifact detected")


def _assert_extra_column_rejected(
    root: Path,
    v5_0_manifest: dict[str, Any],
    frames: dict[str, pd.DataFrame],
    column: str,
) -> None:
    frame = frames["1h"]
    frame[column] = 0
    errors, _quality = _frame_errors(root, v5_0_manifest, "1h", frame)
    assert _errors_contain(errors, "V5.2 label schema mismatch")


def _frame_errors(
    root: Path,
    v5_0_manifest: dict[str, Any],
    timeframe: str,
    frame: pd.DataFrame,
) -> tuple[list[str], dict[str, Any]]:
    input_path = input_ohlcv_path(root, timeframe, v5_0_manifest)
    input_frame = read_parquet(input_path).head(len(frame)).reset_index(drop=True)
    manifest = _load(root / MANIFEST_PATH_V5_2)
    return _validate_label_frame(
        timeframe,
        frame,
        input_path,
        input_frame,
        manifest["label_run_id"],
        expected_rows=len(frame),
    )


def _assert_safety_flag_rejected(manifest_report: tuple[dict[str, Any], dict[str, Any]], flag: str) -> None:
    manifest, _report = manifest_report
    manifest["safety"][flag] = True
    errors = _validate_safety(manifest["safety"])
    assert _errors_contain(errors, f"V5.2 safety flag {flag} must be False")


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("forbidden", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
