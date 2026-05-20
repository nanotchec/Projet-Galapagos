from __future__ import annotations

import json
import shutil
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.multi_day import (
    DATES_V2_9,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    output_path,
    raw_zip_path,
    run_multi_day_public_market_data_v2_9,
)
from galapagos.data.public_market.multi_day_validation import validate_multi_day_public_market_data_v2_9
from galapagos.data.public_market.multi_day_validation import _find_forbidden_v2_9_artifacts
from galapagos.data.public_market.multi_day_validation import _validate_markdown
from galapagos.data.public_market.multi_day_validation import _validate_ohlcv_frame
from galapagos.data.public_market.multi_day_validation import _validate_output_entry
from galapagos.data.public_market.multi_day_validation import _validate_raw_files
from galapagos.data.public_market.multi_day_validation import _validate_report
from galapagos.data.public_market.multi_day_validation import _validate_safety
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet, write_parquet


@pytest.fixture(scope="session")
def valid_v2_9_template_data(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    root = tmp_path_factory.mktemp("valid_v2_9_template")
    workspace = Path(__file__).resolve().parents[2]
    raw_source = workspace / "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m"
    if raw_source.exists():
        for date in DATES_V2_9:
            source = raw_source / f"BTCUSDT-1m-{date}.zip"
            if source.exists():
                target = raw_zip_path(root, date)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    run_multi_day_public_market_data_v2_9(root, no_network=False, validate_previous_layers=False)
    result = validate_multi_day_public_market_data_v2_9(root)
    assert result["passed"], result["errors"]
    return root, result


@pytest.fixture(scope="session")
def valid_v2_9_template(valid_v2_9_template_data: tuple[Path, dict[str, Any]]) -> Path:
    root, _result = valid_v2_9_template_data
    return root


@pytest.fixture(scope="session")
def valid_v2_9_template_validation_result(valid_v2_9_template_data: tuple[Path, dict[str, Any]]) -> dict[str, Any]:
    _root, result = valid_v2_9_template_data
    return deepcopy(result)


@pytest.fixture()
def valid_v2_9_project(tmp_path: Path, valid_v2_9_template: Path) -> Path:
    destination = tmp_path / "project"
    shutil.copytree(valid_v2_9_template, destination)
    return destination


@pytest.fixture()
def valid_v2_9_manifest_report(valid_v2_9_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v2_9_template / MANIFEST_PATH)), deepcopy(_load(valid_v2_9_template / REPORT_JSON_PATH))


@pytest.fixture(scope="session")
def valid_v2_9_frame_cache(valid_v2_9_template: Path) -> dict[str, pd.DataFrame]:
    return {timeframe: read_parquet(output_path(valid_v2_9_template, timeframe)) for timeframe in ["1m", "5m", "15m", "1h"]}


@pytest.fixture()
def valid_v2_9_frames(valid_v2_9_frame_cache: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {timeframe: frame.copy(deep=True) for timeframe, frame in valid_v2_9_frame_cache.items()}


def test_validator_v2_9_accepts_valid_multi_day_data(valid_v2_9_template_validation_result: dict[str, Any]) -> None:
    result = valid_v2_9_template_validation_result
    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v2_9_rejects_missing_raw_zip(valid_v2_9_project: Path) -> None:
    manifest = _load(valid_v2_9_project / MANIFEST_PATH)
    raw_zip_path(valid_v2_9_project, "2024-01-16").unlink()
    errors, _raw_rows = _validate_raw_files(valid_v2_9_project, manifest)
    assert _errors_contain(errors, "missing raw zip")


def test_validator_v2_9_rejects_wrong_raw_checksum(valid_v2_9_project: Path) -> None:
    manifest = _load(valid_v2_9_project / MANIFEST_PATH)
    manifest["raw_files"]["2024-01-16"]["sha256"] = "bad"
    errors, _raw_rows = _validate_raw_files(valid_v2_9_project, manifest)
    assert _errors_contain(errors, "V2.9 raw checksum mismatch")


def test_validator_v2_9_rejects_deleted_1m_row_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "1m")).iloc[:-1].reset_index(drop=True)
    _write_mutated_output(valid_v2_9_project, "1m", frame)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "V2.9 physical quality error for 1m")


def test_validator_v2_9_rejects_duplicate_1m_row_even_with_synced_checksum(valid_v2_9_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v2_9_frames["1m"]
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    errors = _validate_ohlcv_frame("1m", frame)
    assert _errors_contain(errors, "duplicate")


def test_validator_v2_9_rejects_shuffled_1m_parquet_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "1m")).sample(frac=1.0, random_state=42).reset_index(drop=True)
    _write_mutated_output(valid_v2_9_project, "1m", frame)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "monotonic")


def test_validator_v2_9_rejects_extra_future_return_column_even_with_synced_checksum(valid_v2_9_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v2_9_frames["1m"]
    frame["future_return"] = 0.0
    errors = _validate_ohlcv_frame("1m", frame)
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v2_9_rejects_extra_signal_column_even_with_synced_checksum(valid_v2_9_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v2_9_frames["1m"]
    frame["signal"] = 0
    errors = _validate_ohlcv_frame("1m", frame)
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v2_9_rejects_column_order_mismatch_even_with_synced_checksum(valid_v2_9_frames: dict[str, pd.DataFrame]) -> None:
    frame = valid_v2_9_frames["1m"]
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    errors = _validate_ohlcv_frame("1m", frame[columns])
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v2_9_rejects_modified_5m_high_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "5m"))
    frame.loc[0, "high"] = float(frame.loc[0, "high"]) + 100.0
    _write_mutated_output(valid_v2_9_project, "5m", frame)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "parent-child consistency mismatch")


def test_validator_v2_9_rejects_manifest_output_rows_lie(
    valid_v2_9_template: Path,
    valid_v2_9_manifest_report: tuple[dict[str, Any], dict[str, Any]],
    valid_v2_9_frames: dict[str, pd.DataFrame],
) -> None:
    manifest, _report = valid_v2_9_manifest_report
    manifest["outputs"]["5m"]["rows"] = 123
    errors = _validate_output_entry(valid_v2_9_template, manifest, "5m", output_path(valid_v2_9_template, "5m"), valid_v2_9_frames["5m"])
    assert _errors_contain(errors, "V2.9 manifest output mismatch for 5m.rows")


def test_validator_v2_9_rejects_report_output_sha_lie(valid_v2_9_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = valid_v2_9_manifest_report
    report["outputs"]["5m"]["sha256"] = "bad"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "V2.9 quality report mismatch")


def test_validator_v2_9_rejects_markdown_strategy_validated_claim(tmp_path: Path, valid_v2_9_template: Path) -> None:
    path = tmp_path / REPORT_MD_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    source_text = (valid_v2_9_template / REPORT_MD_PATH).read_text(encoding="utf-8")
    path.write_text(source_text + "\nStrategy validated.\n", encoding="utf-8")
    errors = _validate_markdown(tmp_path)
    assert _errors_contain(errors, "V2.9 Markdown report contains forbidden claim")


def test_validator_v2_9_rejects_safety_flag_trading_true(valid_v2_9_manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _report = valid_v2_9_manifest_report
    manifest["safety"]["trading_enabled"] = True
    errors = _validate_safety(manifest["safety"])
    assert _errors_contain(errors, "V2.9 safety flag trading_enabled must be False")


def test_validator_v2_9_rejects_features_v2_9_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v2_9/features/dummy.txt")
    errors = _find_forbidden_v2_9_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V2.9 artifact detected")


def test_validator_v2_9_rejects_labels_v2_9_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v2_9/labels/dummy.txt")
    errors = _find_forbidden_v2_9_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V2.9 artifact detected")


def test_validator_v2_9_rejects_dataset_ml_v2_9_directory_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "data/research/v2_9/datasets/ml/dummy.txt")
    errors = _find_forbidden_v2_9_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V2.9 artifact detected")


def test_validator_v2_9_rejects_backtest_report_created(tmp_path: Path) -> None:
    _touch_forbidden(tmp_path, "reports/backtests/backtest.json")
    errors = _find_forbidden_v2_9_artifacts(tmp_path)
    assert _errors_contain(errors, "Forbidden V2.9 artifact detected")


def _write_mutated_output(root: Path, timeframe: str, frame: pd.DataFrame) -> None:
    path = output_path(root, timeframe)
    write_parquet(frame, path)
    manifest = _load(root / MANIFEST_PATH)
    manifest["outputs"][timeframe]["sha256"] = sha256_file(path)
    manifest["outputs"][timeframe]["bytes"] = path.stat().st_size
    manifest["outputs"][timeframe]["rows"] = int(len(frame))
    _sync_manifest_report(root, manifest)


def _sync_manifest_report(root: Path, manifest: dict[str, Any]) -> None:
    _dump(root / MANIFEST_PATH, manifest)
    _dump(root / REPORT_JSON_PATH, deepcopy(manifest))


def _touch_forbidden(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("forbidden", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
