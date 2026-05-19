from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.datasets.schemas import (
    DATACARD_MD_PATH,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    TARGET_TIMEFRAMES,
    get_dataset_gold_path,
    get_split_gold_path,
)
from galapagos.datasets.validation import validate_offline_supervised_dataset_v2_7

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from run_offline_supervised_dataset_v2_7 import run_offline_supervised_dataset_v2_7


@pytest.fixture(scope="session")
def valid_v2_7_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("valid_v2_7_template")
    workspace = Path(__file__).resolve().parents[2]
    for relative in [
        "data/raw/public_market",
        "data/silver/market_data/ohlcv",
        "data/gold/features",
        "data/gold/labels",
        "reports/manifests",
        "reports/data_quality",
        "reports/features",
        "reports/labels",
    ]:
        _copy_tree(workspace / relative, root / relative)
    run_offline_supervised_dataset_v2_7(root)
    result = validate_offline_supervised_dataset_v2_7(root)
    assert result["passed"], result["errors"]
    return root


@pytest.fixture()
def valid_v2_7_project(tmp_path: Path, valid_v2_7_template: Path) -> Path:
    destination = tmp_path / "project"
    shutil.copytree(valid_v2_7_template, destination)
    return destination


def test_validator_v2_7_accepts_valid_dataset(valid_v2_7_project: Path) -> None:
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v2_7_rejects_extra_prediction_column_even_with_synced_checksum(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "5m")
    frame = pd.read_parquet(path)
    frame["prediction"] = 0.0
    frame.to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "5m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 dataset schema mismatch for 5m")


def test_validator_v2_7_rejects_extra_signal_column_even_with_synced_checksum(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "5m")
    frame = pd.read_parquet(path)
    frame["signal"] = "HOLD"
    frame.to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "5m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 dataset schema mismatch for 5m")


def test_validator_v2_7_rejects_extra_order_column_even_with_synced_checksum(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "5m")
    frame = pd.read_parquet(path)
    frame["order"] = "none"
    frame.to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "5m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 dataset schema mismatch for 5m")


def test_validator_v2_7_rejects_column_order_mismatch_even_with_synced_checksum(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "1m")
    frame = pd.read_parquet(path)
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    frame[columns].to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "1m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 dataset schema mismatch for 1m")


def test_validator_v2_7_rejects_wrong_source_features_sha256_even_with_synced_checksum(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "5m")
    frame = pd.read_parquet(path)
    frame["source_features_sha256"] = "bad"
    frame.to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "5m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "source hashes invalid")


def test_validator_v2_7_rejects_wrong_source_labels_sha256_even_with_synced_checksum(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "5m")
    frame = pd.read_parquet(path)
    frame["source_labels_sha256"] = "bad"
    frame.to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "5m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "source hashes invalid")


def test_validator_v2_7_rejects_modified_feature_value_even_with_synced_checksum(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "15m")
    frame = pd.read_parquet(path)
    frame.loc[30, "return_1"] = 999.0
    frame.to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "15m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 dataset physical mismatch for 15m")


def test_validator_v2_7_rejects_modified_label_value_even_with_synced_checksum(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "15m")
    frame = pd.read_parquet(path)
    frame.loc[0, "future_log_return_h1"] = 999.0
    frame.to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "15m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 dataset physical mismatch for 15m")


def test_validator_v2_7_rejects_feature_available_ts_after_decision_ts(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "1m")
    frame = pd.read_parquet(path)
    frame.loc[0, "feature_available_ts"] = frame.loc[0, "decision_ts"] + pd.Timedelta(minutes=1)
    frame.to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "1m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "feature_available_ts > decision_ts")


def test_validator_v2_7_rejects_label_available_ts_before_or_equal_decision_ts(valid_v2_7_project: Path) -> None:
    path = get_dataset_gold_path(valid_v2_7_project, "1m")
    frame = pd.read_parquet(path)
    frame.loc[0, "label_available_ts"] = frame.loc[0, "decision_ts"]
    frame.to_parquet(path, index=False)
    _sync_dataset_output(valid_v2_7_project, "1m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "label_available_ts <= decision_ts")


def test_validator_v2_7_rejects_temporally_shuffled_split(valid_v2_7_project: Path) -> None:
    path = get_split_gold_path(valid_v2_7_project, "5m")
    frame = pd.read_parquet(path)
    shuffled = pd.concat([frame.iloc[[1]], frame.iloc[[0]], frame.iloc[2:]], ignore_index=True)
    shuffled.to_parquet(path, index=False)
    _sync_split_output(valid_v2_7_project, "5m")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 split physical mismatch for 5m")


def test_validator_v2_7_rejects_report_json_lie(valid_v2_7_project: Path) -> None:
    report = _load(valid_v2_7_project / REPORT_JSON_PATH)
    report["outputs"]["5m"]["sha256"] = "bad"
    _dump(valid_v2_7_project / REPORT_JSON_PATH, report)
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 quality report mismatch")


def test_validator_v2_7_rejects_manifest_unexpected_key(valid_v2_7_project: Path) -> None:
    manifest = _load(valid_v2_7_project / MANIFEST_PATH)
    manifest["strategy_validated"] = True
    _dump(valid_v2_7_project / MANIFEST_PATH, manifest)
    _dump(valid_v2_7_project / REPORT_JSON_PATH, manifest)
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 manifest unexpected keys")


def test_validator_v2_7_rejects_report_unexpected_key(valid_v2_7_project: Path) -> None:
    report = _load(valid_v2_7_project / REPORT_JSON_PATH)
    report["claim"] = "strategy validated"
    _dump(valid_v2_7_project / REPORT_JSON_PATH, report)
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 quality report unexpected keys")


def test_validator_v2_7_rejects_markdown_strategy_validated_claim(valid_v2_7_project: Path) -> None:
    path = valid_v2_7_project / REPORT_MD_PATH
    path.write_text(path.read_text(encoding="utf-8") + "\nStrategy validated.\n", encoding="utf-8")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 Markdown report contains forbidden claim")


def test_validator_v2_7_rejects_datacard_strategy_validated_claim(valid_v2_7_project: Path) -> None:
    path = valid_v2_7_project / DATACARD_MD_PATH
    path.write_text(path.read_text(encoding="utf-8") + "\nStrategy validated.\n", encoding="utf-8")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 data card contains forbidden claim")


def test_validator_v2_7_rejects_safety_flag_ml_true(valid_v2_7_project: Path) -> None:
    _mutate_safety(valid_v2_7_project, "ml_enabled", True)
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 safety flag ml_enabled must be False")


def test_validator_v2_7_rejects_safety_flag_backtest_true(valid_v2_7_project: Path) -> None:
    _mutate_safety(valid_v2_7_project, "backtest_enabled", True)
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 safety flag backtest_enabled must be False")


def test_validator_v2_7_rejects_safety_flag_trading_true(valid_v2_7_project: Path) -> None:
    _mutate_safety(valid_v2_7_project, "trading_enabled", True)
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 safety flag trading_enabled must be False")


def test_validator_v2_7_rejects_safety_flag_orders_true(valid_v2_7_project: Path) -> None:
    _mutate_safety(valid_v2_7_project, "orders_enabled", True)
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "V2.7 safety flag orders_enabled must be False")


def test_validator_v2_7_rejects_model_file_created(valid_v2_7_project: Path) -> None:
    model_path = valid_v2_7_project / "models/model.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_text("not allowed", encoding="utf-8")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "Forbidden")


def test_validator_v2_7_rejects_backtest_report_created(valid_v2_7_project: Path) -> None:
    report_path = valid_v2_7_project / "reports/backtests/backtest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("{}", encoding="utf-8")
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert _failed_with(result, "Forbidden")


def test_validator_v2_7_allows_dataset_outputs_only_in_v2_7_paths(valid_v2_7_project: Path) -> None:
    for timeframe in TARGET_TIMEFRAMES:
        assert get_dataset_gold_path(valid_v2_7_project, timeframe).exists()
        assert get_split_gold_path(valid_v2_7_project, timeframe).exists()
    result = validate_offline_supervised_dataset_v2_7(valid_v2_7_project)
    assert result["passed"] is True


def _copy_tree(src: Path, dest: Path) -> None:
    if not src.exists():
        return
    for item in src.rglob("*"):
        if item.is_file() and "__pycache__" not in item.parts and ".pytest_cache" not in item.parts:
            target = dest / item.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sync_dataset_output(root: Path, timeframe: str) -> None:
    manifest = _load(root / MANIFEST_PATH)
    path = get_dataset_gold_path(root, timeframe)
    manifest["outputs"][timeframe]["sha256"] = sha256_file(path)
    manifest["outputs"][timeframe]["bytes"] = path.stat().st_size
    manifest["outputs"][timeframe]["rows"] = len(pd.read_parquet(path))
    _dump(root / MANIFEST_PATH, manifest)
    _dump(root / REPORT_JSON_PATH, manifest)


def _sync_split_output(root: Path, timeframe: str) -> None:
    manifest = _load(root / MANIFEST_PATH)
    path = get_split_gold_path(root, timeframe)
    manifest["splits"][timeframe]["sha256"] = sha256_file(path)
    manifest["splits"][timeframe]["bytes"] = path.stat().st_size
    manifest["splits"][timeframe]["rows"] = len(pd.read_parquet(path))
    _dump(root / MANIFEST_PATH, manifest)
    _dump(root / REPORT_JSON_PATH, manifest)


def _mutate_safety(root: Path, key: str, value: bool) -> None:
    manifest = _load(root / MANIFEST_PATH)
    manifest["safety"][key] = value
    _dump(root / MANIFEST_PATH, manifest)
    _dump(root / REPORT_JSON_PATH, manifest)


def _failed_with(result: dict, text: str) -> bool:
    assert result["passed"] is False
    return any(text in error for error in result["errors"])
