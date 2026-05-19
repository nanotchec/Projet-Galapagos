from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.provenance import sha256_file
from galapagos.labels.schemas import LABEL_COLUMNS_V2_6
from galapagos.labels.registry import (
    MANIFEST_PATH,
    QUALITY_JSON_PATH,
    QUALITY_MD_PATH,
    TARGET_TIMEFRAMES,
    get_label_gold_path,
)
from galapagos.labels.validation import validate_label_factory_v2_6


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
def valid_v2_6_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    # Set up a session template by copying data/reports/docs/src from workspace
    root = tmp_path_factory.mktemp("valid_v2_6_template")
    workspace = Path(__file__).resolve().parents[2]
    
    for folder in ["data", "reports", "docs"]:
        _copy_dir_without_cache(workspace / folder, root / folder)
        
    _copy_dir_without_cache(workspace / "src", root / "src")
    _copy_dir_without_cache(workspace / "scripts", root / "scripts")
    
    # Run a quick check to make sure the template's baseline validation passes
    res = validate_label_factory_v2_6(root)
    assert res["passed"] is True, f"Template V2.6 baseline validation failed: {res['errors']}"
    return root


@pytest.fixture()
def project_v2_6(tmp_path: Path, valid_v2_6_template: Path) -> Path:
    # A functional clone for each test to apply mutations to
    destination = tmp_path / "project_v2_6_test"
    destination.mkdir(parents=True, exist_ok=True)
    
    # We only need data, reports, and docs for the validator to run
    for folder in ["data", "reports", "docs"]:
        src_folder = valid_v2_6_template / folder
        if src_folder.exists():
            for item in src_folder.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(valid_v2_6_template)
                    target = destination / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
    return destination


def test_validator_nominal_case(project_v2_6: Path):
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is True
    assert len(res["errors"]) == 0


def test_validator_missing_manifest(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    assert manifest_file.exists()
    manifest_file.unlink()
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("Manifest V2.6 not found" in err for err in res["errors"])


def test_validator_manifest_version_mismatch(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
        
    # Corrupt version
    manifest_corrupt = copy.deepcopy(manifest)
    manifest_corrupt["version"] = "V2.5"
    with open(manifest_file, "w") as f:
        json.dump(manifest_corrupt, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("Manifest version mismatch" in err for err in res["errors"])


def test_validator_safety_trading_enabled(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
        
    # Corrupt safety
    manifest["safety"]["trading_enabled"] = True
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("trading_enabled must be False" in err for err in res["errors"])


def test_validator_limitations_claim_modified(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
        
    # Corrupt limitations
    manifest["limitations"] = ["Claim edited or missing"]
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest limitations mismatch" in err for err in res["errors"])


def test_validator_output_checksum_mismatch(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
        
    # Corrupt output checksum for '1m'
    manifest["outputs"]["1m"]["sha256"] = "falsified_sha256_hash_value"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest output mismatch for 1m.sha256" in err for err in res["errors"])


def test_validator_row_count_mismatch(project_v2_6: Path):
    # Alter the parquet file to have one less row
    output_path = get_label_gold_path(project_v2_6, "1m")
    df = pd.read_parquet(output_path)
    df_altered = df.iloc[:-1]  # remove last row
    df_altered.to_parquet(output_path, index=False)
    
    # Resynchronize manifest output checksum so it doesn't fail on checksum first
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["outputs"]["1m"]["sha256"] = sha256_file(output_path)
    # also resynchronize bytes in manifest to avoid bytes mismatch
    manifest["outputs"]["1m"]["bytes"] = output_path.stat().st_size
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("row count mismatch for 1m" in err or "V2.6 manifest output mismatch for 1m.rows" in err for err in res["errors"])


def test_validator_column_order_mismatch(project_v2_6: Path):
    # Swap columns in parquet
    output_path = get_label_gold_path(project_v2_6, "1m")
    df = pd.read_parquet(output_path)
    cols = list(df.columns)
    # swap first two columns
    cols[0], cols[1] = cols[1], cols[0]
    df_altered = df[cols]
    df_altered.to_parquet(output_path, index=False)
    
    # Resynchronize manifest output checksum
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["outputs"]["1m"]["sha256"] = sha256_file(output_path)
    manifest["outputs"]["1m"]["bytes"] = output_path.stat().st_size
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("Label schema mismatch or column order incorrect for 1m" in err for err in res["errors"])


def test_validator_forbidden_column_in_parquet(project_v2_6: Path):
    # Add a forbidden column like 'strategy_signal'
    output_path = get_label_gold_path(project_v2_6, "1m")
    df = pd.read_parquet(output_path)
    df["strategy_signal"] = 1.0
    df.to_parquet(output_path, index=False)
    
    # Resynchronize manifest output checksum
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["outputs"]["1m"]["sha256"] = sha256_file(output_path)
    manifest["outputs"]["1m"]["bytes"] = output_path.stat().st_size
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("Forbidden column detected in Parquet" in err or "Label schema mismatch" in err for err in res["errors"])


def test_validator_mathematical_mismatch(project_v2_6: Path):
    # Alter return value for first row
    output_path = get_label_gold_path(project_v2_6, "1m")
    df = pd.read_parquet(output_path)
    df.loc[0, "future_simple_return_h1"] = 999.9  # corrupt value
    df.to_parquet(output_path, index=False)
    
    # Resynchronize manifest output checksum
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["outputs"]["1m"]["sha256"] = sha256_file(output_path)
    manifest["outputs"]["1m"]["bytes"] = output_path.stat().st_size
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("future_simple_return_h1 mathematical mismatch on 1m" in err for err in res["errors"])


def test_validator_causal_leakage(project_v2_6: Path):
    # Set label_available_ts <= decision_ts
    output_path = get_label_gold_path(project_v2_6, "1m")
    df = pd.read_parquet(output_path)
    df.loc[0, "label_available_ts"] = df.loc[0, "decision_ts"]  # force leakage
    df.to_parquet(output_path, index=False)
    
    # Resynchronize manifest output checksum
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["outputs"]["1m"]["sha256"] = sha256_file(output_path)
    manifest["outputs"]["1m"]["bytes"] = output_path.stat().st_size
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("Causal leakage detected" in err for err in res["errors"])


def test_validator_forbidden_column_in_feature_store(project_v2_6: Path):
    # Alter the gold feature store Parquet file by injecting a label column
    feature_gold_path = project_v2_6 / "data/gold/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/year=2024/month=01/features-2024-01-15.parquet"
    if feature_gold_path.exists():
        df = pd.read_parquet(feature_gold_path)
        df["future_close_h1"] = 100.0  # forbidden column in features!
        df.to_parquet(feature_gold_path, index=False)
        
        res = validate_label_factory_v2_6(project_v2_6)
        assert res["passed"] is False
        assert any("Leakage: Label column" in err for err in res["errors"])


def test_validator_forbidden_claim_in_markdown(project_v2_6: Path):
    report_file = project_v2_6 / QUALITY_MD_PATH
    assert report_file.exists()
    
    with open(report_file, "r") as f:
        content = f.read()
        
    # Inject a forbidden claim like "strategy validated = true"
    content_corrupt = content + "\n\nWe have successfully done strategy validated = true on the model.\n"
    with open(report_file, "w") as f:
        f.write(content_corrupt)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 Markdown report contains forbidden claim" in err for err in res["errors"])


def test_validator_ml_dataset_directory_present(project_v2_6: Path):
    # Creating a strictly forbidden dataset ML directory
    forbidden_dir = project_v2_6 / "data/gold/dataset_ml"
    forbidden_dir.mkdir(parents=True, exist_ok=True)
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("Violation: ML dataset directory" in err for err in res["errors"])


# --- PART G MANDATORY TESTS V2.6.1 ---

def test_validator_v2_6_rejects_manifest_unexpected_strategy_validated_key(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["strategy_validated"] = True
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest unexpected keys" in err for err in res["errors"])


def test_validator_v2_6_rejects_report_unexpected_claim_key(project_v2_6: Path):
    report_file = project_v2_6 / QUALITY_JSON_PATH
    with open(report_file, "r") as f:
        report = json.load(f)
    report["claim"] = "strategy validated"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 quality report unexpected keys" in err for err in res["errors"])


def test_validator_v2_6_rejects_report_outputs_checksum_lie(project_v2_6: Path):
    report_file = project_v2_6 / QUALITY_JSON_PATH
    with open(report_file, "r") as f:
        report = json.load(f)
    report["outputs"]["5m"]["sha256"] = "bad"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 quality report mismatch for outputs" in err for err in res["errors"])


def test_validator_v2_6_rejects_report_quality_rows_lie(project_v2_6: Path):
    report_file = project_v2_6 / QUALITY_JSON_PATH
    with open(report_file, "r") as f:
        report = json.load(f)
    report["quality"]["5m"]["rows"] = 123
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 quality report mismatch for quality" in err for err in res["errors"])


def test_validator_v2_6_rejects_report_threshold_lie(project_v2_6: Path):
    report_file = project_v2_6 / QUALITY_JSON_PATH
    with open(report_file, "r") as f:
        report = json.load(f)
    report["threshold"] = 0.1
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 quality report mismatch for threshold" in err for err in res["errors"])


def test_validator_v2_6_rejects_report_horizons_lie(project_v2_6: Path):
    report_file = project_v2_6 / QUALITY_JSON_PATH
    with open(report_file, "r") as f:
        report = json.load(f)
    report["horizons"] = [1, 2, 3]
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 quality report mismatch for horizons" in err for err in res["errors"])


def test_validator_v2_6_rejects_manifest_outputs_rows_lie(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["outputs"]["5m"]["rows"] = 123
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest output mismatch for 5m.rows" in err for err in res["errors"])


def test_validator_v2_6_rejects_manifest_outputs_sha_lie(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["outputs"]["5m"]["sha256"] = "bad"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest output mismatch for 5m.sha256" in err for err in res["errors"])


def test_validator_v2_6_rejects_manifest_input_rows_lie(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["input_ohlcv"]["5m"]["rows"] = 123
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest input mismatch for 5m.rows" in err for err in res["errors"])


def test_validator_v2_6_rejects_manifest_quality_valid_count_lie(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    manifest["quality"]["5m"]["valid_counts_by_horizon"]["h1"] = 999
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest quality mismatch for 5m.valid_counts_by_horizon.h1" in err for err in res["errors"])


def test_validator_v2_6_rejects_synced_limitations_strategy_validated_claim(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    report_file = project_v2_6 / QUALITY_JSON_PATH
    
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    with open(report_file, "r") as f:
        report = json.load(f)
        
    manifest["limitations"] = ["strategy validated"]
    report["limitations"] = ["strategy validated"]
    
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("forbidden claim" in err or "V2.6 manifest limitations mismatch" in err for err in res["errors"])


def test_validator_v2_6_rejects_empty_synced_limitations(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    report_file = project_v2_6 / QUALITY_JSON_PATH
    
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    with open(report_file, "r") as f:
        report = json.load(f)
        
    manifest["limitations"] = []
    report["limitations"] = []
    
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest limitations mismatch" in err for err in res["errors"])


def test_validator_v2_6_rejects_invalid_created_at_even_if_report_synced(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    report_file = project_v2_6 / QUALITY_JSON_PATH
    
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    with open(report_file, "r") as f:
        report = json.load(f)
        
    manifest["created_at_utc"] = "not-a-date"
    report["created_at_utc"] = "not-a-date"
    
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest created_at_utc invalid" in err for err in res["errors"])


def test_validator_v2_6_rejects_invalid_label_run_id_even_if_report_synced(project_v2_6: Path):
    manifest_file = project_v2_6 / MANIFEST_PATH
    report_file = project_v2_6 / QUALITY_JSON_PATH
    
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
    with open(report_file, "r") as f:
        report = json.load(f)
        
    manifest["label_run_id"] = "bogus"
    report["label_run_id"] = "bogus"
    
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 manifest label_run_id invalid" in err for err in res["errors"])


def test_validator_v2_6_rejects_markdown_strategy_validated_claim(project_v2_6: Path):
    report_file = project_v2_6 / QUALITY_MD_PATH
    assert report_file.exists()
    
    with open(report_file, "r") as f:
        content = f.read()
        
    content_corrupt = content + "\nStrategy validated.\n"
    with open(report_file, "w") as f:
        f.write(content_corrupt)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is False
    assert any("V2.6 Markdown report contains forbidden claim" in err for err in res["errors"])


def test_validator_v2_6_allows_markdown_negative_claims(project_v2_6: Path):
    report_file = project_v2_6 / QUALITY_MD_PATH
    assert report_file.exists()
    
    with open(report_file, "r") as f:
        content = f.read()
        
    content_valid = content + "\nAucun trading. V2.6 ne valide aucune strategie. Aucun ordre.\n"
    with open(report_file, "w") as f:
        f.write(content_valid)
        
    res = validate_label_factory_v2_6(project_v2_6)
    assert res["passed"] is True
