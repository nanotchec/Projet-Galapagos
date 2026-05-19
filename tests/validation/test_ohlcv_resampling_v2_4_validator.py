from __future__ import annotations

import copy
import json
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from galapagos.data.public_market.config import PublicMarketIngestionConfig
from galapagos.data.public_market.ingestion import run_public_market_ingestion
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.validation.resampling import (
    EXPECTED_LIMITATIONS_V2_4,
    MANIFEST_PATH,
    QUALITY_JSON_PATH,
    resampled_silver_path,
    run_ohlcv_resampling_v2_4,
    validate_ohlcv_resampling_v2_4,
)


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
def valid_v2_4_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("valid_v2_4_template")
    _prepare_valid_resampling(root)
    _copy_dir_without_cache(Path("src"), root / "src")
    _copy_dir_without_cache(Path("scripts"), root / "scripts")
    res = validate_ohlcv_resampling_v2_4(root)
    assert res["passed"] is True, f"Template validation failed: {res['errors']}"
    return root


@pytest.fixture()
def valid_v2_4_project(tmp_path: Path, valid_v2_4_template: Path) -> Path:
    destination = tmp_path / "project_minimal"
    destination.mkdir(parents=True, exist_ok=True)
    for folder in ["data", "reports"]:
        src_folder = valid_v2_4_template / folder
        if src_folder.exists():
            for item in src_folder.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(valid_v2_4_template)
                    target = destination / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
    _sync_copied_ingestion_manifest(destination)
    return destination


@pytest.fixture()
def valid_v2_4_project_with_sources(tmp_path: Path, valid_v2_4_template: Path) -> Path:
    destination = tmp_path / "project_full"
    destination.mkdir(parents=True, exist_ok=True)
    for item in valid_v2_4_template.rglob("*"):
        if item.is_file():
            rel = item.relative_to(valid_v2_4_template)
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
    _sync_copied_ingestion_manifest(destination)
    return destination


@pytest.fixture()
def valid_manifest_report(valid_v2_4_template: Path) -> tuple[dict, dict]:
    manifest = json.loads((valid_v2_4_template / MANIFEST_PATH).read_text(encoding="utf-8"))
    report = json.loads((valid_v2_4_template / QUALITY_JSON_PATH).read_text(encoding="utf-8"))
    return copy.deepcopy(manifest), copy.deepcopy(report)


@pytest.fixture(autouse=True)
def monkeypatch_scans_if_mutation(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if "runs_full_scans" not in request.node.name:
        import galapagos.validation.safety as safety_module
        import galapagos.validation.resampling as resampling_module
        monkeypatch.setattr(safety_module, "scan_new_modules_for_forbidden_terms", lambda root: [])
        monkeypatch.setattr(resampling_module, "_scan_v2_4_scripts", lambda root: [])
        if "included_v2_3" not in request.node.name:
            import galapagos.validation.market_data as market_data_module
            monkeypatch.setattr(
                market_data_module,
                "validate_public_market_ingestion_v2_3",
                lambda root: {"passed": True, "errors": [], "manifest": {}},
            )


# --- Famille A : Intégration Complète ---

def test_validator_v2_4_accepts_valid_resampling_runs_full_scans(valid_v2_4_project_with_sources: Path) -> None:
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project_with_sources)
    assert result["passed"] is True
    assert result["manifest"]["outputs"]["5m"]["rows"] == 288
    assert result["manifest"]["outputs"]["15m"]["rows"] == 96
    assert result["manifest"]["outputs"]["1h"]["rows"] == 24


def test_validator_v2_4_rejects_modified_5m_high_even_with_synced_checksum(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "5m"))
    frame.loc[0, "high"] = frame.loc[0, "high"] + 100
    _write_output_and_sync_manifest(valid_v2_4_project, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("5m parent-child mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_extra_strategy_validated_column_in_5m_even_with_synced_checksum(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "5m"))
    frame["strategy_validated"] = True
    _write_output_and_sync_manifest(valid_v2_4_project, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("5m unexpected columns" in error for error in result["errors"])


def test_validator_v2_4_rejects_extra_future_return_column_in_input_1m_even_with_all_synced_checksums(valid_v2_4_project: Path) -> None:
    config = _config(valid_v2_4_project)
    frame = read_parquet(config.silver_path)
    frame["future_return"] = 0.123
    write_parquet(frame, config.silver_path)
    _sync_copied_ingestion_manifest(valid_v2_4_project)
    manifest_v2_4 = json.loads((valid_v2_4_project / MANIFEST_PATH).read_text(encoding="utf-8"))
    manifest_v2_4["input_1m"]["sha256"] = sha256_file(config.silver_path)
    manifest_v2_4["input_1m"]["bytes"] = config.silver_path.stat().st_size
    (valid_v2_4_project / MANIFEST_PATH).write_text(json.dumps(manifest_v2_4, indent=2) + "\n", encoding="utf-8")
    report_v2_4 = json.loads((valid_v2_4_project / QUALITY_JSON_PATH).read_text(encoding="utf-8"))
    report_v2_4["input_1m"]["sha256"] = manifest_v2_4["input_1m"]["sha256"]
    report_v2_4["input_1m"]["bytes"] = manifest_v2_4["input_1m"]["bytes"]
    (valid_v2_4_project / QUALITY_JSON_PATH).write_text(json.dumps(report_v2_4, indent=2) + "\n", encoding="utf-8")
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("silver unexpected columns" in error or "V2.3.1 input validation failed" in error for error in result["errors"])


def test_validator_v2_4_rejects_included_v2_3_manifest_strategy_validated_claim(valid_v2_4_project: Path) -> None:
    config = _config(valid_v2_4_project)
    manifest = json.loads(config.manifest_path.read_text(encoding="utf-8"))
    manifest["strategy_validated"] = True
    config.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("V2.3 manifest unexpected keys" in error for error in result["errors"])


def test_validator_v2_4_rejects_safety_flag_trading_true(valid_v2_4_project: Path) -> None:
    manifest = json.loads((valid_v2_4_project / MANIFEST_PATH).read_text(encoding="utf-8"))
    manifest["trading_enabled"] = True
    (valid_v2_4_project / MANIFEST_PATH).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert "trading_enabled must be false" in result["errors"]


def test_validator_v2_4_rejects_markdown_forbidden_strategy_claim(valid_v2_4_project: Path) -> None:
    markdown_path = valid_v2_4_project / "reports/data_quality/ohlcv_resampling_v2_4.md"
    markdown_path.write_text(markdown_path.read_text(encoding="utf-8") + "\nStrategy validated.\n", encoding="utf-8")
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert "quality markdown contains forbidden claim: strategy validated" in result["errors"]


def test_validator_v2_4_rejects_quality_report_output_checksum_lie(valid_v2_4_project: Path) -> None:
    report = json.loads((valid_v2_4_project / QUALITY_JSON_PATH).read_text(encoding="utf-8"))
    report["outputs"]["5m"]["sha256"] = "bad"
    (valid_v2_4_project / QUALITY_JSON_PATH).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert "quality report outputs mismatch" in result["errors"]


# --- Famille B : Autres intégrations réduites ou physiques ---

def test_validator_v2_4_rejects_modified_15m_volume_even_with_synced_checksum(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "15m"))
    frame.loc[0, "volume"] = frame.loc[0, "volume"] + 1
    _write_output_and_sync_manifest(valid_v2_4_project, "15m", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("15m parent-child mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_modified_1h_close_even_with_synced_checksum(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "1h"))
    frame.loc[0, "close"] = frame.loc[0, "close"] + 1
    _write_output_and_sync_manifest(valid_v2_4_project, "1h", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("1h parent-child mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_deleted_resampled_row_even_with_synced_checksum(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "5m")).drop(index=1).reset_index(drop=True)
    _write_output_and_sync_manifest(valid_v2_4_project, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("5m row count mismatch" in error or "5m rows mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_shuffled_resampled_parquet_even_with_synced_checksum(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "5m")).sample(frac=1.0, random_state=11).reset_index(drop=True)
    _write_output_and_sync_manifest(valid_v2_4_project, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("5m physical event_ts is not monotonic" in error for error in result["errors"])


def test_validator_v2_4_rejects_wrong_raw_file_sha256_in_resampled_silver(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "5m"))
    frame.loc[:, "raw_file_sha256"] = "wrong"
    _write_output_and_sync_manifest(valid_v2_4_project, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("5m provenance raw_file_sha256 mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_wrong_ingestion_run_id_in_resampled_silver(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "15m"))
    frame.loc[:, "ingestion_run_id"] = "wrong"
    _write_output_and_sync_manifest(valid_v2_4_project, "15m", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("15m provenance ingestion_run_id mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_extra_future_return_column_in_15m_even_with_synced_checksum(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "15m"))
    frame["future_return"] = 0.123
    _write_output_and_sync_manifest(valid_v2_4_project, "15m", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("15m unexpected columns" in error for error in result["errors"])


def test_validator_v2_4_rejects_extra_trading_enabled_column_in_1h_even_with_synced_checksum(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "1h"))
    frame["trading_enabled"] = True
    _write_output_and_sync_manifest(valid_v2_4_project, "1h", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("1h unexpected columns" in error for error in result["errors"])


def test_validator_v2_4_rejects_resampled_column_order_mismatch_even_with_synced_checksum(valid_v2_4_project: Path) -> None:
    frame = read_parquet(resampled_silver_path(valid_v2_4_project, "5m"))
    cols = list(frame.columns)
    cols[0], cols[1] = cols[1], cols[0]
    frame = frame[cols]
    _write_output_and_sync_manifest(valid_v2_4_project, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(valid_v2_4_project)
    assert result["passed"] is False
    assert any("5m column order mismatch" in error for error in result["errors"])


# --- Famille C : Tests Unitaires Ultra-rapides en Mémoire ---

def test_validator_v2_4_rejects_wrong_expected_rows(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["expected_rows"]["5m"] = 999
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("expected rows mismatch for 5m" in error for error in errors)


def test_validator_v2_4_rejects_manifest_quality_rows_lie_even_if_report_synced(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    physical_qualities = copy.deepcopy(manifest["quality"])
    manifest["quality"]["5m"]["rows"] = 123
    from galapagos.validation.resampling import _validate_manifest_quality
    errors = _validate_manifest_quality(manifest, physical_qualities)
    assert any("V2.4 manifest quality mismatch for 5m.rows" in error for error in errors)


def test_validator_v2_4_rejects_manifest_quality_gap_count_lie_even_if_report_synced(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    physical_qualities = copy.deepcopy(manifest["quality"])
    manifest["quality"]["15m"]["gap_count"] = 99
    from galapagos.validation.resampling import _validate_manifest_quality
    errors = _validate_manifest_quality(manifest, physical_qualities)
    assert any("V2.4 manifest quality mismatch for 15m.gap_count" in error for error in errors)


def test_validator_v2_4_rejects_manifest_quality_monotonic_lie_even_if_report_synced(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    physical_qualities = copy.deepcopy(manifest["quality"])
    manifest["quality"]["1h"]["monotonic_event_ts"] = False
    from galapagos.validation.resampling import _validate_manifest_quality
    errors = _validate_manifest_quality(manifest, physical_qualities)
    assert any("V2.4 manifest quality mismatch for 1h.monotonic_event_ts" in error for error in errors)



def test_validator_v2_4_rejects_quality_report_input_sha_lie(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["input_1m"]["sha256"] = "bad"
    from galapagos.validation.resampling import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report input_1m mismatch" in error for error in errors)


def test_validator_v2_4_rejects_quality_report_expected_rows_lie(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["expected_rows"]["5m"] = 999
    from galapagos.validation.resampling import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report expected_rows mismatch" in error for error in errors)


def test_validator_v2_4_rejects_quality_report_parent_child_lie(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["parent_child_consistency"] = False
    from galapagos.validation.resampling import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report parent_child_consistency mismatch" in error for error in errors)


def test_validator_v2_4_rejects_quality_report_resampling_run_id_lie(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["resampling_run_id"] = "wrong"
    from galapagos.validation.resampling import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report resampling_run_id mismatch" in error for error in errors)


def test_validator_v2_4_rejects_quality_report_created_at_lie(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["created_at_utc"] = "1970-01-01T00:00:00Z"
    from galapagos.validation.resampling import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report created_at_utc mismatch" in error for error in errors)


def test_validator_v2_4_rejects_quality_report_limitations_lie(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["limitations"] = []
    from galapagos.validation.resampling import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report limitations mismatch" in error for error in errors)


def test_validator_v2_4_rejects_quality_report_unexpected_top_level_key(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["claim"] = "strategy validated"
    from galapagos.validation.resampling import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report unexpected keys" in error for error in errors)


def test_validator_v2_4_rejects_quality_report_top_level_trading_enabled_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["trading_enabled"] = True
    from galapagos.validation.resampling import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report unexpected keys" in error for error in errors)


def test_validator_v2_4_rejects_manifest_unexpected_top_level_key(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["strategy_validated"] = True
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("V2.4 manifest unexpected keys" in error for error in errors)


def test_validator_v2_4_rejects_manifest_unexpected_execution_key(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["execution_enabled"] = True
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("V2.4 manifest unexpected keys" in error for error in errors)


def test_validator_v2_4_rejects_output_unexpected_key(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["outputs"]["5m"]["claim"] = "ok"
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("V2.4 manifest outputs.5m unexpected keys" in error for error in errors)


def test_validator_v2_4_rejects_quality_unexpected_key(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["quality"]["5m"]["claim"] = "ok"
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("V2.4 manifest quality.5m unexpected keys" in error for error in errors)


def test_validator_v2_4_rejects_report_safety_unexpected_key(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    report["safety"]["execution_enabled"] = True
    from galapagos.validation.resampling import _validate_report
    errors = _validate_report(manifest, report)
    assert any("quality report safety unexpected keys" in error for error in errors)


def test_validator_v2_4_rejects_synced_limitations_strategy_validated_claim(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["limitations"].append("strategy validated")
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("forbidden claim" in error or "V2.4 manifest limitations mismatch" in error for error in errors)


def test_validator_v2_4_rejects_synced_limitations_trading_enabled_claim(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["limitations"].append("trading enabled")
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("forbidden claim" in error or "V2.4 manifest limitations mismatch" in error for error in errors)


def test_validator_v2_4_rejects_empty_synced_limitations(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["limitations"] = []
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("V2.4 manifest limitations mismatch" in error for error in errors)


def test_validator_v2_4_rejects_invalid_created_at_even_if_report_synced(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["created_at_utc"] = "not-a-date"
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("V2.4 manifest created_at_utc invalid" in error for error in errors)


def test_validator_v2_4_rejects_invalid_resampling_run_id_even_if_report_synced(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["resampling_run_id"] = "bogus"
    from galapagos.validation.resampling import _validate_manifest
    errors = _validate_manifest(Path("."), manifest)
    assert any("V2.4 manifest resampling_run_id invalid" in error for error in errors)


def test_validator_v2_4_allows_expected_limitations(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    assert manifest["limitations"] == EXPECTED_LIMITATIONS_V2_4
    assert report["limitations"] == EXPECTED_LIMITATIONS_V2_4


def test_validator_v2_4_rejects_included_v2_3_quality_report_strategy_claim(valid_v2_4_project: Path) -> None:
    from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
    from galapagos.data.public_market.config import PublicMarketIngestionConfig
    
    config = PublicMarketIngestionConfig(
        source="binance_archive",
        market_type="spot",
        symbol="BTCUSDT",
        timeframe="1m",
        date="2024-01-15",
        output_root=valid_v2_4_project,
    )
    report = _load_json(config.quality_json_path)
    report["claim"] = "strategy validated"
    _write_json(config.quality_json_path, report)
    
    res = validate_public_market_ingestion_v2_3(valid_v2_4_project)
    assert res["passed"] is False
    assert any("V2.3 quality report unexpected keys" in error or "forbidden claim" in error for error in res["errors"])



def test_validator_v2_4_rejects_included_v2_3_markdown_strategy_claim(valid_v2_4_project: Path) -> None:
    from galapagos.validation.market_data import validate_public_market_ingestion_v2_3
    from galapagos.data.public_market.config import PublicMarketIngestionConfig
    
    config = PublicMarketIngestionConfig(
        source="binance_archive",
        market_type="spot",
        symbol="BTCUSDT",
        timeframe="1m",
        date="2024-01-15",
        output_root=valid_v2_4_project,
    )
    config.quality_md_path.write_text(
        config.quality_md_path.read_text(encoding="utf-8") + "\nStrategy validated.\n",
        encoding="utf-8",
    )
    
    res = validate_public_market_ingestion_v2_3(valid_v2_4_project)
    assert res["passed"] is False
    assert any("V2.3 quality markdown contains forbidden claim" in error for error in res["errors"])


def test_validator_v2_4_rejects_safety_flag_ml_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["ml_enabled"] = True
    from galapagos.validation.resampling import validate_safety_flags
    errors = validate_safety_flags(manifest)
    assert any("ml_enabled must be false" in error for error in errors)


def test_validator_v2_4_rejects_safety_flag_labels_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["labels_enabled"] = True
    from galapagos.validation.resampling import validate_safety_flags
    errors = validate_safety_flags(manifest)
    assert any("labels_enabled must be false" in error for error in errors)


def test_validator_v2_4_rejects_safety_flag_backtest_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["backtest_enabled"] = True
    from galapagos.validation.resampling import validate_safety_flags
    errors = validate_safety_flags(manifest)
    assert any("backtest_enabled must be false" in error for error in errors)


def test_validator_v2_4_rejects_safety_flag_orders_true(valid_manifest_report) -> None:
    manifest, report = valid_manifest_report
    manifest["orders_enabled"] = True
    from galapagos.validation.resampling import validate_safety_flags
    errors = validate_safety_flags(manifest)
    assert any("orders_enabled must be false" in error for error in errors)


def test_validator_v2_4_allows_markdown_negative_safety_claims(valid_manifest_report) -> None:
    # On teste validate_markdown_forbidden_claims
    from galapagos.validation.safety import validate_markdown_forbidden_claims
    text = "Aucun trading. V2.4 ne valide aucune stratégie. Aucun ordre."
    errors = validate_markdown_forbidden_claims(text, "quality markdown")
    assert not errors


# --- Helpers & setup ---

def _assert_safety_flag_rejected(tmp_path: Path, field: str, expected_error: str) -> None:
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest[field] = True
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert expected_error in result["errors"]


def _prepare_valid_resampling(tmp_path: Path) -> None:
    if (tmp_path / MANIFEST_PATH).exists() and (tmp_path / QUALITY_JSON_PATH).exists():
        return
    _write_raw_zip(tmp_path, minutes=1440)
    manifest = run_public_market_ingestion(_config(tmp_path))
    assert manifest["status"] == "PASS"
    resampling_manifest = run_ohlcv_resampling_v2_4(tmp_path)
    assert resampling_manifest["status"] == "PASS"


def _sync_copied_ingestion_manifest(root: Path) -> None:
    config = _config(root)
    manifest = _load_json(config.manifest_path)
    manifest["raw"]["path"] = str(config.raw_path.relative_to(root))
    manifest["raw"]["sha256"] = sha256_file(config.raw_path)
    manifest["raw"]["bytes"] = config.raw_path.stat().st_size
    manifest["silver"]["path"] = str(config.silver_path.relative_to(root))
    manifest["silver"]["sha256"] = sha256_file(config.silver_path)
    manifest["silver"]["bytes"] = config.silver_path.stat().st_size
    _write_json(config.manifest_path, manifest)
    report = _load_json(config.quality_json_path)
    report["raw_checksum"] = manifest["raw"]["sha256"]
    report["silver_checksum"] = manifest["silver"]["sha256"]
    report["raw_path"] = manifest["raw"]["path"]
    report["silver_path"] = manifest["silver"]["path"]
    _write_json(config.quality_json_path, report)


def _config(tmp_path: Path) -> PublicMarketIngestionConfig:
    return PublicMarketIngestionConfig(
        source="binance_archive",
        market_type="spot",
        symbol="BTCUSDT",
        timeframe="1m",
        date="2024-01-15",
        output_root=tmp_path,
        no_network=True,
    )


def _write_output_and_sync_manifest(tmp_path: Path, timeframe: str, frame: pd.DataFrame) -> None:
    path = resampled_silver_path(tmp_path, timeframe)
    write_parquet(frame, path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["outputs"][timeframe]["sha256"] = sha256_file(path)
    manifest["outputs"][timeframe]["bytes"] = path.stat().st_size
    manifest["outputs"][timeframe]["rows"] = len(frame)
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["outputs"] = manifest["outputs"]
    _write_json(tmp_path / QUALITY_JSON_PATH, report)


def _set_manifest_and_report_quality_field(tmp_path: Path, timeframe: str, field: str, value: object) -> None:
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["quality"][timeframe][field] = value
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["quality"][timeframe][field] = value
    _write_json(tmp_path / QUALITY_JSON_PATH, report)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_raw_zip(tmp_path: Path, *, minutes: int) -> Path:
    config = _config(tmp_path)
    config.raw_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(config.raw_path, "w") as archive:
        archive.writestr("BTCUSDT-1m-2024-01-15.csv", _csv_rows(minutes=minutes))
    return config.raw_path


def _csv_rows(*, minutes: int) -> str:
    rows = []
    start = pd.Timestamp("2024-01-15T00:00:00Z")
    for index in range(minutes):
        open_ts = int((start + pd.Timedelta(minutes=index)).timestamp() * 1000)
        close_ts = int((start + pd.Timedelta(minutes=index, seconds=59, milliseconds=999)).timestamp() * 1000)
        open_price = 42000.0 + (index / 100)
        rows.append(
            ",".join(
                [
                    str(open_ts),
                    f"{open_price:.2f}",
                    f"{open_price + 10:.2f}",
                    f"{open_price - 10:.2f}",
                    f"{open_price + 1:.2f}",
                    "12.5",
                    str(close_ts),
                    "525000.0",
                    str(100 + index),
                    "6.25",
                    "262500.0",
                    "0",
                ]
            )
        )
    return "\n".join(rows) + "\n"
