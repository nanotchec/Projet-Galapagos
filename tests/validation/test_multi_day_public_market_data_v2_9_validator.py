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
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet, write_parquet


@pytest.fixture(scope="session")
def valid_v2_9_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
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
    return root


@pytest.fixture()
def valid_v2_9_project(tmp_path: Path, valid_v2_9_template: Path) -> Path:
    destination = tmp_path / "project"
    shutil.copytree(valid_v2_9_template, destination)
    return destination


@pytest.fixture()
def valid_v2_9_manifest_report(valid_v2_9_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v2_9_template / MANIFEST_PATH)), deepcopy(_load(valid_v2_9_template / REPORT_JSON_PATH))


def test_validator_v2_9_accepts_valid_multi_day_data(valid_v2_9_template: Path) -> None:
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_template)
    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v2_9_rejects_missing_raw_zip(valid_v2_9_project: Path) -> None:
    raw_zip_path(valid_v2_9_project, "2024-01-16").unlink()
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "missing raw zip")


def test_validator_v2_9_rejects_wrong_raw_checksum(valid_v2_9_project: Path) -> None:
    manifest = _load(valid_v2_9_project / MANIFEST_PATH)
    manifest["raw_files"]["2024-01-16"]["sha256"] = "bad"
    _sync_manifest_report(valid_v2_9_project, manifest)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "V2.9 raw checksum mismatch")


def test_validator_v2_9_rejects_deleted_1m_row_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "1m")).iloc[:-1].reset_index(drop=True)
    _write_mutated_output(valid_v2_9_project, "1m", frame)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "V2.9 physical quality error for 1m")


def test_validator_v2_9_rejects_duplicate_1m_row_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "1m"))
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    _write_mutated_output(valid_v2_9_project, "1m", frame)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "duplicate")


def test_validator_v2_9_rejects_shuffled_1m_parquet_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "1m")).sample(frac=1.0, random_state=42).reset_index(drop=True)
    _write_mutated_output(valid_v2_9_project, "1m", frame)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "monotonic")


def test_validator_v2_9_rejects_extra_future_return_column_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "1m"))
    frame["future_return"] = 0.0
    _write_mutated_output(valid_v2_9_project, "1m", frame)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "schema mismatch")


def test_validator_v2_9_rejects_extra_signal_column_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "1m"))
    frame["signal"] = 0
    _write_mutated_output(valid_v2_9_project, "1m", frame)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "schema mismatch")


def test_validator_v2_9_rejects_column_order_mismatch_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "1m"))
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    _write_mutated_output(valid_v2_9_project, "1m", frame[columns])
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "schema mismatch")


def test_validator_v2_9_rejects_modified_5m_high_even_with_synced_checksum(valid_v2_9_project: Path) -> None:
    frame = read_parquet(output_path(valid_v2_9_project, "5m"))
    frame.loc[0, "high"] = float(frame.loc[0, "high"]) + 100.0
    _write_mutated_output(valid_v2_9_project, "5m", frame)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "parent-child consistency mismatch")


def test_validator_v2_9_rejects_manifest_output_rows_lie(valid_v2_9_project: Path) -> None:
    manifest = _load(valid_v2_9_project / MANIFEST_PATH)
    report = deepcopy(manifest)
    manifest["outputs"]["5m"]["rows"] = 123
    report["outputs"]["5m"]["rows"] = 123
    _dump(valid_v2_9_project / MANIFEST_PATH, manifest)
    _dump(valid_v2_9_project / REPORT_JSON_PATH, report)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "V2.9 manifest output mismatch for 5m.rows")


def test_validator_v2_9_rejects_report_output_sha_lie(valid_v2_9_project: Path) -> None:
    report = _load(valid_v2_9_project / REPORT_JSON_PATH)
    report["outputs"]["5m"]["sha256"] = "bad"
    _dump(valid_v2_9_project / REPORT_JSON_PATH, report)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "V2.9 quality report mismatch")


def test_validator_v2_9_rejects_markdown_strategy_validated_claim(valid_v2_9_project: Path) -> None:
    path = valid_v2_9_project / REPORT_MD_PATH
    path.write_text(path.read_text(encoding="utf-8") + "\nStrategy validated.\n", encoding="utf-8")
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "V2.9 Markdown report contains forbidden claim")


def test_validator_v2_9_rejects_safety_flag_trading_true(valid_v2_9_project: Path) -> None:
    manifest = _load(valid_v2_9_project / MANIFEST_PATH)
    manifest["safety"]["trading_enabled"] = True
    _sync_manifest_report(valid_v2_9_project, manifest)
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "V2.9 safety flag trading_enabled must be False")


def test_validator_v2_9_rejects_features_v2_9_directory_created(valid_v2_9_project: Path) -> None:
    _touch_forbidden(valid_v2_9_project, "data/research/v2_9/features/dummy.txt")
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "Forbidden V2.9 artifact detected")


def test_validator_v2_9_rejects_labels_v2_9_directory_created(valid_v2_9_project: Path) -> None:
    _touch_forbidden(valid_v2_9_project, "data/research/v2_9/labels/dummy.txt")
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "Forbidden V2.9 artifact detected")


def test_validator_v2_9_rejects_dataset_ml_v2_9_directory_created(valid_v2_9_project: Path) -> None:
    _touch_forbidden(valid_v2_9_project, "data/research/v2_9/datasets/ml/dummy.txt")
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "Forbidden V2.9 artifact detected")


def test_validator_v2_9_rejects_backtest_report_created(valid_v2_9_project: Path) -> None:
    _touch_forbidden(valid_v2_9_project, "reports/backtests/backtest.json")
    result = validate_multi_day_public_market_data_v2_9(valid_v2_9_project)
    assert _errors_contain(result["errors"], "Forbidden V2.9 artifact detected")


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
