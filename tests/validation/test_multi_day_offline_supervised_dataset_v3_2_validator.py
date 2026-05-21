from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.datasets.multi_day import input_feature_path, input_label_path, run_multi_day_offline_supervised_dataset_v3_2
from galapagos.datasets.multi_day_validation import (
    _find_forbidden_v3_2_artifacts,
    _validate_dataset_temporal_rules,
    _validate_dataset_values_against_sources,
    _validate_manifest_structure,
    _validate_markdown,
    _validate_report,
    _validate_safety,
    _validate_timeframe,
    validate_multi_day_offline_supervised_dataset_v3_2,
)
from galapagos.datasets.schemas import (
    MANIFEST_PATH_V3_2,
    REPORT_JSON_PATH_V3_2,
    REPORT_MD_PATH_V3_2,
    DATACARD_MD_PATH_V3_2,
    get_dataset_v3_2_path,
)


@pytest.fixture(scope="session")
def valid_v3_2_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("valid_v3_2_template")
    workspace = Path(__file__).resolve().parents[2]
    for relative in [
        "data/research/v3_0/features/ohlcv",
        "data/research/v3_1/labels/forward_returns",
    ]:
        shutil.copytree(workspace / relative, root / relative)
    run_multi_day_offline_supervised_dataset_v3_2(root, validate_recent_layers=False)
    result = validate_multi_day_offline_supervised_dataset_v3_2(root)
    assert result["passed"], result["errors"]
    return root


@pytest.fixture()
def valid_v3_2_project(tmp_path: Path, valid_v3_2_template: Path) -> Path:
    destination = tmp_path / "project"
    shutil.copytree(valid_v3_2_template, destination)
    return destination


@pytest.fixture()
def manifest_report(valid_v3_2_template: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return deepcopy(_load(valid_v3_2_template / MANIFEST_PATH_V3_2)), deepcopy(_load(valid_v3_2_template / REPORT_JSON_PATH_V3_2))


def test_validator_v3_2_accepts_valid_dataset(valid_v3_2_project: Path) -> None:
    result = validate_multi_day_offline_supervised_dataset_v3_2(valid_v3_2_project)
    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v3_2_rejects_extra_prediction_column_even_with_synced_checksum(valid_v3_2_project: Path) -> None:
    _add_column(valid_v3_2_project, "5m", "prediction", 0.0)
    errors = _validate_single_timeframe(valid_v3_2_project, "5m")
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v3_2_rejects_extra_signal_column_even_with_synced_checksum(valid_v3_2_project: Path) -> None:
    _add_column(valid_v3_2_project, "5m", "signal", "HOLD")
    errors = _validate_single_timeframe(valid_v3_2_project, "5m")
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v3_2_rejects_extra_order_column_even_with_synced_checksum(valid_v3_2_project: Path) -> None:
    _add_column(valid_v3_2_project, "5m", "order", "none")
    errors = _validate_single_timeframe(valid_v3_2_project, "5m")
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v3_2_rejects_column_order_mismatch_even_with_synced_checksum(valid_v3_2_project: Path) -> None:
    path = get_dataset_v3_2_path(valid_v3_2_project, "1m")
    frame = pd.read_parquet(path)
    columns = list(frame.columns)
    columns[0], columns[1] = columns[1], columns[0]
    frame[columns].to_parquet(path, index=False)
    _sync_dataset_output(valid_v3_2_project, "1m")
    errors = _validate_single_timeframe(valid_v3_2_project, "1m")
    assert _errors_contain(errors, "schema mismatch")


def test_validator_v3_2_rejects_wrong_source_features_sha256_even_with_synced_checksum(valid_v3_2_project: Path) -> None:
    _mutate_dataset(valid_v3_2_project, "5m", lambda frame: frame.assign(source_features_sha256="bad"))
    errors = _validate_single_timeframe(valid_v3_2_project, "5m")
    assert _errors_contain(errors, "source hashes invalid") or _errors_contain(errors, "physical mismatch")


def test_validator_v3_2_rejects_wrong_source_labels_sha256_even_with_synced_checksum(valid_v3_2_project: Path) -> None:
    _mutate_dataset(valid_v3_2_project, "5m", lambda frame: frame.assign(source_labels_sha256="bad"))
    errors = _validate_single_timeframe(valid_v3_2_project, "5m")
    assert _errors_contain(errors, "source hashes invalid") or _errors_contain(errors, "physical mismatch")


def test_validator_v3_2_rejects_modified_feature_value_even_with_synced_checksum(valid_v3_2_project: Path) -> None:
    def mutate(frame: pd.DataFrame) -> pd.DataFrame:
        frame.loc[30, "return_1"] = 999.0
        return frame

    _mutate_dataset(valid_v3_2_project, "15m", mutate)
    errors = _validate_single_timeframe(valid_v3_2_project, "15m")
    assert _errors_contain(errors, "physical mismatch") or _errors_contain(errors, "feature source mismatch")


def test_validator_v3_2_rejects_modified_label_value_even_with_synced_checksum(valid_v3_2_project: Path) -> None:
    def mutate(frame: pd.DataFrame) -> pd.DataFrame:
        frame.loc[0, "future_log_return_h1"] = 999.0
        return frame

    _mutate_dataset(valid_v3_2_project, "15m", mutate)
    errors = _validate_single_timeframe(valid_v3_2_project, "15m")
    assert _errors_contain(errors, "physical mismatch") or _errors_contain(errors, "label source mismatch")


def test_validator_v3_2_rejects_feature_available_ts_after_decision_ts(valid_v3_2_project: Path) -> None:
    frame = pd.read_parquet(get_dataset_v3_2_path(valid_v3_2_project, "1m")).head(12).copy()
    frame.loc[0, "feature_available_ts"] = frame.loc[0, "decision_ts"] + pd.Timedelta(minutes=1)
    errors = _validate_dataset_temporal_rules(frame, "1m")
    assert _errors_contain(errors, "feature_available_ts > decision_ts")


def test_validator_v3_2_rejects_label_available_ts_before_or_equal_decision_ts(valid_v3_2_project: Path) -> None:
    frame = pd.read_parquet(get_dataset_v3_2_path(valid_v3_2_project, "1m")).head(12).copy()
    frame.loc[0, "label_available_ts"] = frame.loc[0, "decision_ts"]
    errors = _validate_dataset_temporal_rules(frame, "1m")
    assert _errors_contain(errors, "label_available_ts <= decision_ts")


def test_validator_v3_2_rejects_temporally_shuffled_split(valid_v3_2_project: Path) -> None:
    frame = pd.read_parquet(get_dataset_v3_2_path(valid_v3_2_project, "1m")).head(12).copy()
    frame.loc[0, "split"] = "test"
    errors = _validate_dataset_temporal_rules(frame, "1m")
    assert _errors_contain(errors, "split temporal order invalid")


def test_validator_v3_2_rejects_report_json_lie(manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = manifest_report
    report["outputs"]["1m"]["rows"] = -1
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "quality report mismatch")


def test_validator_v3_2_rejects_manifest_unexpected_key(manifest_report: tuple[dict[str, Any], dict[str, Any]], valid_v3_2_template: Path) -> None:
    manifest, _ = manifest_report
    manifest["unexpected"] = "no"
    errors = _validate_manifest_structure(valid_v3_2_template, manifest)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v3_2_rejects_report_unexpected_key(manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, report = manifest_report
    report["unexpected"] = "no"
    errors = _validate_report(manifest, report)
    assert _errors_contain(errors, "unexpected keys")


def test_validator_v3_2_rejects_markdown_strategy_validated_claim(valid_v3_2_project: Path) -> None:
    (valid_v3_2_project / REPORT_MD_PATH_V3_2).write_text("strategy validated\n", encoding="utf-8")
    assert _errors_contain(_validate_markdown(valid_v3_2_project), "forbidden claim")


def test_validator_v3_2_rejects_datacard_strategy_validated_claim(valid_v3_2_project: Path) -> None:
    (valid_v3_2_project / DATACARD_MD_PATH_V3_2).write_text("strategy validated\n", encoding="utf-8")
    assert _errors_contain(_validate_markdown(valid_v3_2_project), "forbidden claim")


def test_validator_v3_2_rejects_safety_flag_ml_true(manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _ = manifest_report
    manifest["safety"]["ml_enabled"] = True
    assert _errors_contain(_validate_safety(manifest["safety"]), "ml_enabled")


def test_validator_v3_2_rejects_safety_flag_backtest_true(manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _ = manifest_report
    manifest["safety"]["backtest_enabled"] = True
    assert _errors_contain(_validate_safety(manifest["safety"]), "backtest_enabled")


def test_validator_v3_2_rejects_safety_flag_trading_true(manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _ = manifest_report
    manifest["safety"]["trading_enabled"] = True
    assert _errors_contain(_validate_safety(manifest["safety"]), "trading_enabled")


def test_validator_v3_2_rejects_safety_flag_orders_true(manifest_report: tuple[dict[str, Any], dict[str, Any]]) -> None:
    manifest, _ = manifest_report
    manifest["safety"]["orders_enabled"] = True
    assert _errors_contain(_validate_safety(manifest["safety"]), "orders_enabled")


def test_validator_v3_2_rejects_model_file_created(valid_v3_2_project: Path) -> None:
    path = valid_v3_2_project / "models/model_v3_2.pkl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"forbidden")
    assert _errors_contain(_find_forbidden_v3_2_artifacts(valid_v3_2_project), "Forbidden V3.2")


def test_validator_v3_2_rejects_backtest_report_created(valid_v3_2_project: Path) -> None:
    path = valid_v3_2_project / "reports/backtests/backtest_v3_2.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    assert _errors_contain(_find_forbidden_v3_2_artifacts(valid_v3_2_project), "Forbidden V3.2")


def test_validator_v3_2_allows_dataset_outputs_only_in_v3_2_paths(valid_v3_2_project: Path) -> None:
    errors = _find_forbidden_v3_2_artifacts(valid_v3_2_project)
    assert not _errors_contain(errors, "data/research/v3_2/datasets")


def test_validator_v3_2_value_helper_detects_source_changes(valid_v3_2_project: Path) -> None:
    dataset = pd.read_parquet(get_dataset_v3_2_path(valid_v3_2_project, "1h")).copy()
    features = pd.read_parquet(input_feature_path(valid_v3_2_project, "1h")).copy()
    labels = pd.read_parquet(input_label_path(valid_v3_2_project, "1h")).copy()
    dataset.loc[0, "return_1"] = 123.0
    errors = _validate_dataset_values_against_sources(
        "1h",
        dataset,
        features,
        labels,
        dataset["dataset_run_id"].iloc[0],
        sha256_file(input_feature_path(valid_v3_2_project, "1h")),
        sha256_file(input_label_path(valid_v3_2_project, "1h")),
    )
    assert _errors_contain(errors, "physical mismatch")


def _add_column(root: Path, timeframe: str, column: str, value: Any) -> None:
    _mutate_dataset(root, timeframe, lambda frame: frame.assign(**{column: value}))


def _mutate_dataset(root: Path, timeframe: str, mutate: Any) -> None:
    path = get_dataset_v3_2_path(root, timeframe)
    frame = pd.read_parquet(path)
    mutate(frame).to_parquet(path, index=False)
    _sync_dataset_output(root, timeframe)


def _validate_single_timeframe(root: Path, timeframe: str) -> list[str]:
    manifest = _load(root / MANIFEST_PATH_V3_2)
    quality: dict[str, dict[str, Any]] = {}
    return _validate_timeframe(root, manifest, timeframe, quality)


def _sync_dataset_output(root: Path, timeframe: str) -> None:
    path = get_dataset_v3_2_path(root, timeframe)
    manifest = _load(root / MANIFEST_PATH_V3_2)
    manifest["outputs"][timeframe]["sha256"] = sha256_file(path)
    manifest["outputs"][timeframe]["bytes"] = path.stat().st_size
    manifest["outputs"][timeframe]["rows"] = len(pd.read_parquet(path))
    _write(root / MANIFEST_PATH_V3_2, manifest)
    _write(root / REPORT_JSON_PATH_V3_2, manifest)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def _errors_contain(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
