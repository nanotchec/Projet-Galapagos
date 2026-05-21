from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.validation.resampling import resampled_silver_path
from galapagos.features.schemas import FEATURE_COLUMNS_V2_5
from galapagos.features.registry import (
    MANIFEST_PATH,
    QUALITY_JSON_PATH,
    QUALITY_MD_PATH,
    TARGET_TIMEFRAMES,
    get_feature_gold_path,
)
from galapagos.features.causal_ohlcv import build_causal_features
from galapagos.features.validation import validate_causal_feature_store_v2_5


def _copy_dir_without_cache(src: Path, dest: Path) -> None:
    if not src.exists():
        return
    for item in src.rglob("*"):
        if "__pycache__" in item.parts or ".pytest_cache" in item.parts or ".git" in item.parts or ".venv" in item.parts:
            continue
        if item.is_file():
            rel = item.relative_to(src)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


@pytest.fixture(scope="session")
def valid_v2_5_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("valid_v2_5_template")
    
    # Resolve the project root dynamically to support clean zip extractions
    workspace = Path(__file__).resolve().parents[2]
    
    # 1. Copy required data (raw, silver V2.4)
    for folder in ["data", "reports", "docs"]:
        _copy_dir_without_cache(workspace / folder, root / folder)
        
    _copy_dir_without_cache(workspace / "src", root / "src")
    _copy_dir_without_cache(workspace / "scripts", root / "scripts")
    
    # 2. Run feature generation for V2.5 in the template
    feature_run_id = "v2_5_20260519T210000Z_abcdef12"
    
    # Generate gold features from silver OHLCV
    for tf in TARGET_TIMEFRAMES:
        input_path = resampled_silver_path(root, tf)
        output_path = get_feature_gold_path(root, tf)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df_silver = read_parquet(input_path)
        sha_silver = sha256_file(input_path)
        
        df_gold = build_causal_features(df_silver, sha_silver, feature_run_id)
        write_parquet(df_gold, output_path)
        
    # Write a nominal manifest/report mock for the template
    # Let's generate a temporary manifest to make the validation pass
    import sys
    import importlib.util
    script_path = workspace / "scripts" / "run_causal_feature_store_v2_5.py"
    spec = importlib.util.spec_from_file_location("run_causal_feature_store_v2_5", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_causal_feature_store_v2_5"] = module
    spec.loader.exec_module(module)
    run_feature_store_generation = module.run_feature_store_generation
    run_feature_store_generation(root, feature_run_id=feature_run_id)
    
    res = validate_causal_feature_store_v2_5(root)
    assert res["passed"] is True, f"Template V2.5 validation failed: {res['errors']}"
    return root


@pytest.fixture()
def valid_v2_5_project(tmp_path: Path, valid_v2_5_template: Path) -> Path:
    destination = tmp_path / "project_minimal"
    destination.mkdir(parents=True, exist_ok=True)
    for folder in ["data", "reports", "docs"]:
        src_folder = valid_v2_5_template / folder
        if src_folder.exists():
            for item in src_folder.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(valid_v2_5_template)
                    target = destination / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
    return destination


@pytest.fixture()
def valid_v2_5_project_with_sources(tmp_path: Path, valid_v2_5_template: Path) -> Path:
    destination = tmp_path / "project_full"
    destination.mkdir(parents=True, exist_ok=True)
    for item in valid_v2_5_template.rglob("*"):
        if item.is_file():
            rel = item.relative_to(valid_v2_5_template)
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
    return destination


@pytest.fixture()
def valid_manifest_report(valid_v2_5_template: Path) -> tuple[dict, dict]:
    manifest = json.loads((valid_v2_5_template / MANIFEST_PATH).read_text(encoding="utf-8"))
    report = json.loads((valid_v2_5_template / QUALITY_JSON_PATH).read_text(encoding="utf-8"))
    return copy.deepcopy(manifest), copy.deepcopy(report)


@pytest.fixture(autouse=True)
def monkeypatch_scans_if_mutation(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if "runs_full_scans" not in request.node.name:
        import galapagos.validation.safety as safety_module
        import galapagos.features.validation as features_validation_module
        monkeypatch.setattr(safety_module, "scan_new_modules_for_forbidden_terms", lambda root: [])
        monkeypatch.setattr(features_validation_module, "_scan_v2_5_scripts", lambda root: [])


# --- Famille A : Intégration Physique ---

def test_validator_v2_5_accepts_valid_feature_store_runs_full_scans(valid_v2_5_project_with_sources: Path) -> None:
    result = validate_causal_feature_store_v2_5(valid_v2_5_project_with_sources)
    assert result["passed"] is True
    assert result["manifest"]["outputs"]["1m"]["rows"] == 1440
    assert result["manifest"]["outputs"]["5m"]["rows"] == 288


def test_validator_v2_5_rejects_extra_future_return_column_even_with_synced_checksum(valid_v2_5_project: Path) -> None:
    gold_path = get_feature_gold_path(valid_v2_5_project, "5m")
    df = read_parquet(gold_path)
    df["future_return"] = 0.05
    _write_output_and_sync_manifest(valid_v2_5_project, "5m", df)
    
    result = validate_causal_feature_store_v2_5(valid_v2_5_project)
    assert result["passed"] is False
    assert any("unexpected columns" in err or "forbidden term" in err for err in result["errors"])


def test_validator_v2_5_rejects_extra_label_column_even_with_synced_checksum(valid_v2_5_project: Path) -> None:
    gold_path = get_feature_gold_path(valid_v2_5_project, "15m")
    df = read_parquet(gold_path)
    df["label_direction"] = 1.0
    _write_output_and_sync_manifest(valid_v2_5_project, "15m", df)
    
    result = validate_causal_feature_store_v2_5(valid_v2_5_project)
    assert result["passed"] is False
    assert any("unexpected columns" in err or "forbidden term" in err for err in result["errors"])


def test_validator_v2_5_rejects_extra_signal_column_even_with_synced_checksum(valid_v2_5_project: Path) -> None:
    gold_path = get_feature_gold_path(valid_v2_5_project, "1h")
    df = read_parquet(gold_path)
    df["signal_buy"] = True
    _write_output_and_sync_manifest(valid_v2_5_project, "1h", df)
    
    result = validate_causal_feature_store_v2_5(valid_v2_5_project)
    assert result["passed"] is False
    assert any("unexpected columns" in err or "forbidden term" in err for err in result["errors"])


def test_validator_v2_5_rejects_column_order_mismatch_even_with_synced_checksum(valid_v2_5_project: Path) -> None:
    gold_path = get_feature_gold_path(valid_v2_5_project, "5m")
    df = read_parquet(gold_path)
    # Shuffle columns order
    cols = list(df.columns)
    cols[0], cols[1] = cols[1], cols[0]
    df = df[cols]
    _write_output_and_sync_manifest(valid_v2_5_project, "5m", df)
    
    result = validate_causal_feature_store_v2_5(valid_v2_5_project)
    assert result["passed"] is False
    assert any("column order mismatch" in err for err in result["errors"])


def test_validator_v2_5_rejects_wrong_source_ohlcv_sha256_even_with_synced_checksum(valid_v2_5_project: Path) -> None:
    gold_path = get_feature_gold_path(valid_v2_5_project, "5m")
    df = read_parquet(gold_path)
    df["source_ohlcv_sha256"] = "wrong-sha"
    _write_output_and_sync_manifest(valid_v2_5_project, "5m", df)
    
    result = validate_causal_feature_store_v2_5(valid_v2_5_project)
    assert result["passed"] is False
    assert any("source_ohlcv_sha256 mismatch" in err for err in result["errors"])


def test_validator_v2_5_rejects_feature_available_ts_before_available_ts(valid_v2_5_project: Path) -> None:
    gold_path = get_feature_gold_path(valid_v2_5_project, "5m")
    df = read_parquet(gold_path)
    df["feature_available_ts"] = "2024-01-15T00:00:00Z" # force it to the past
    _write_output_and_sync_manifest(valid_v2_5_project, "5m", df)
    
    result = validate_causal_feature_store_v2_5(valid_v2_5_project)
    assert result["passed"] is False
    assert any("feature_available_ts < available_ts" in err for err in result["errors"])


def test_validator_v2_5_rejects_decision_ts_before_feature_available_ts(valid_v2_5_project: Path) -> None:
    gold_path = get_feature_gold_path(valid_v2_5_project, "5m")
    df = read_parquet(gold_path)
    df["decision_ts"] = "2024-01-15T00:00:00Z" # force it to the past
    _write_output_and_sync_manifest(valid_v2_5_project, "5m", df)
    
    result = validate_causal_feature_store_v2_5(valid_v2_5_project)
    assert result["passed"] is False
    assert any("decision_ts < feature_available_ts" in err for err in result["errors"])


def test_validator_v2_5_rejects_markdown_strategy_validated_claim(valid_v2_5_project: Path) -> None:
    md_file = valid_v2_5_project / QUALITY_MD_PATH
    content = md_file.read_text(encoding="utf-8") + "\nStrategy validated by model.\n"
    md_file.write_text(content, encoding="utf-8")
    
    result = validate_causal_feature_store_v2_5(valid_v2_5_project)
    assert result["passed"] is False
    assert any("contains forbidden claim" in err for err in result["errors"])


# --- Famille B : Tests Unitaires Logiques en Mémoire ---

def test_validator_v2_5_rejects_report_json_lie(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["feature_run_id"] = "v2_5_20260519T000000Z_00000000"
    from galapagos.features.validation import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report feature_run_id mismatch" in err for err in errors)


def test_validator_v2_5_rejects_manifest_unexpected_key(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["strategy_validated"] = True
    from galapagos.features.validation import _validate_manifest_structure
    errors = _validate_manifest_structure(Path("."), manifest)
    assert any("unexpected keys" in err for err in errors)


def test_validator_v2_5_rejects_report_unexpected_key(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["prediction_type"] = "none"
    from galapagos.features.validation import _validate_report
    errors = _validate_report(manifest, report)
    assert any("unexpected keys" in err for err in errors)


def test_validator_v2_5_rejects_safety_flag_ml_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["ml_enabled"] = True
    from galapagos.features.validation import _validate_manifest_structure
    errors = _validate_manifest_structure(Path("."), manifest)
    assert any("ml_enabled must be false" in err for err in errors)


def test_validator_v2_5_rejects_safety_flag_labels_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["labels_enabled"] = True
    from galapagos.features.validation import _validate_manifest_structure
    errors = _validate_manifest_structure(Path("."), manifest)
    assert any("labels_enabled must be false" in err for err in errors)


def test_validator_v2_5_rejects_safety_flag_backtest_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["backtest_enabled"] = True
    from galapagos.features.validation import _validate_manifest_structure
    errors = _validate_manifest_structure(Path("."), manifest)
    assert any("backtest_enabled must be false" in err for err in errors)


def test_validator_v2_5_rejects_safety_flag_trading_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["trading_enabled"] = True
    from galapagos.features.validation import _validate_manifest_structure
    errors = _validate_manifest_structure(Path("."), manifest)
    assert any("trading_enabled must be false" in err for err in errors)


def test_validator_v2_5_rejects_safety_flag_orders_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["orders_enabled"] = True
    from galapagos.features.validation import _validate_manifest_structure
    errors = _validate_manifest_structure(Path("."), manifest)
    assert any("orders_enabled must be false" in err for err in errors)


# --- Helpers & setup ---

def _write_output_and_sync_manifest(tmp_path: Path, timeframe: str, frame: pd.DataFrame) -> None:
    path = get_feature_gold_path(tmp_path, timeframe)
    write_parquet(frame, path)
    
    manifest_path = tmp_path / MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    manifest["outputs"][timeframe]["sha256"] = sha256_file(path)
    manifest["outputs"][timeframe]["bytes"] = path.stat().st_size
    manifest["outputs"][timeframe]["rows"] = len(frame)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    
    quality_path = tmp_path / QUALITY_JSON_PATH
    report = json.loads(quality_path.read_text(encoding="utf-8"))
    report["outputs"] = manifest["outputs"]
    quality_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_no_hardcoded_local_project_path_in_v2_5_validator_tests() -> None:
    # Verify that there are no hardcoded local absolute paths to Lilian's machine
    test_file = Path(__file__).resolve()
    content = test_file.read_text(encoding="utf-8")
    part1 = "/Users/" + "lilianserre"
    part2 = "/Documents/projets/projet-galapagos"
    forbidden = part1 + part2
    
    # We scan the file content excluding comments/lines containing our own verification tokens
    occurrences = [
        line for line in content.splitlines()
        if forbidden in line and "part1 =" not in line and "part2 =" not in line and "forbidden =" not in line
    ]
    assert len(occurrences) == 0, f"Hardcoded local project path found in test file: {occurrences}"

