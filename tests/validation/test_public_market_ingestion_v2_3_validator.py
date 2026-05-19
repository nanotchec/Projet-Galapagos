from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd

from galapagos.data.public_market.config import PublicMarketIngestionConfig
from galapagos.data.public_market.ingestion import run_public_market_ingestion
from galapagos.data.public_market.provenance import sha256_file
from galapagos.data.public_market.quality import assess_ohlcv_quality
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.validation.market_data import validate_public_market_ingestion_v2_3


def test_validator_accepts_valid_physical_ingestion(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is True
    assert result["physical_quality"]["rows"] == 1440


def test_validator_rejects_wrong_raw_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest_path = _config(tmp_path).manifest_path
    manifest = _load_json(manifest_path)
    manifest["raw"]["sha256"] = "0" * 64
    _write_json(manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "raw checksum mismatch" in result["errors"]


def test_validator_rejects_manifest_pass_with_corrupted_silver_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path)
    frame.loc[0, "close"] = frame.loc[0, "close"] + 1
    write_parquet(frame, _config(tmp_path).silver_path)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "silver checksum mismatch" in result["errors"]


def test_validator_rejects_deleted_row_gap_even_with_synced_manifest_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path).drop(index=10).reset_index(drop=True)
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("gap" in error.lower() or "row count" in error.lower() for error in result["errors"])


def test_validator_rejects_shuffled_silver_even_with_synced_manifest_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path).sample(frac=1.0, random_state=23).reset_index(drop=True)
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("monotonic" in error.lower() or "physical order" in error.lower() for error in result["errors"])


def test_validator_rejects_raw_silver_mismatch_even_with_synced_raw_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    _rewrite_raw_zip_with_first_open(tmp_path, "43000.00")
    config = _config(tmp_path)
    manifest = _load_json(config.manifest_path)
    manifest["raw"]["sha256"] = sha256_file(config.raw_path)
    manifest["raw"]["bytes"] = config.raw_path.stat().st_size
    _write_json(config.manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("raw/silver mismatch" in error.lower() for error in result["errors"])


def test_validator_rejects_normalized_file_sha256_column_if_present(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path)
    frame["normalized_file_sha256"] = "stale"
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "silver must not contain normalized_file_sha256" in result["errors"]


def test_validator_rejects_stale_walk_forward_candidate_scope_in_project_state(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    stale = {
        "last_validated_version": "V2.2.1",
        "candidate_version": "V2.3.1",
        "authorized_future_scope": "bounded_offline_walk_forward_protocol_no_network_no_real_trading_no_paper_live",
        "approval_phrase_expected_exact": "J'approuve V2.3 protocole walk-forward offline borné, sans réseau, sans trading réel, sans paper live.",
    }
    for relative in [Path("reports/PROJECT_STATE.json"), Path("reports/current/latest_metrics.json")]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, stale)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("stale v2.3 candidate scope" in error.lower() for error in result["errors"])


def test_validator_rejects_incomplete_row_count_even_if_manifest_synced(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path).drop(index=100).reset_index(drop=True)
    _write_silver_and_sync_quality_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("row count mismatch" in error.lower() or "rows 1439" in error.lower() for error in result["errors"])


def test_validator_rejects_wrong_raw_file_sha256_in_silver_even_with_synced_silver_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path)
    frame.loc[:, "raw_file_sha256"] = "bad-sha"
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("raw_file_sha256 mismatch" in error for error in result["errors"])


def test_validator_rejects_wrong_ingestion_run_id_in_silver_even_with_synced_silver_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path)
    frame.loc[:, "ingestion_run_id"] = "wrong-run"
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("ingestion_run_id mismatch" in error for error in result["errors"])


def test_validator_rejects_wrong_ingested_at_ts_in_silver_even_with_synced_silver_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path)
    frame.loc[:, "ingested_at_ts"] = pd.Timestamp("2024-01-01T00:00:00Z")
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("ingested_at_ts mismatch" in error for error in result["errors"])


def test_validator_rejects_duplicate_row_even_with_synced_manifest_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("duplicate" in error.lower() for error in result["errors"])


def test_validator_rejects_negative_volume_even_with_synced_manifest_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path)
    frame.loc[0, "volume"] = -1.0
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("negative volume" in error.lower() for error in result["errors"])


def test_validator_rejects_ohlc_violation_even_with_synced_manifest_checksum(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path)
    frame.loc[0, "high"] = frame.loc[0, "low"] - 1
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("ohlc" in error.lower() for error in result["errors"])


def test_validator_rejects_missing_critical_column(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    frame = read_parquet(_config(tmp_path).silver_path).drop(columns=["event_ts"])
    _write_silver_and_sync_basic_manifest(tmp_path, frame)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert any("missing columns" in error.lower() for error in result["errors"])


def test_validator_rejects_safety_flag_authentication_true(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest_path = _config(tmp_path).manifest_path
    manifest = _load_json(manifest_path)
    manifest["authentication_used"] = True
    _write_json(manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "authentication_used must be false" in result["errors"]


def test_validator_rejects_safety_flag_api_key_true(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest = _load_json(_config(tmp_path).manifest_path)
    manifest["api_key_used"] = True
    _write_json(_config(tmp_path).manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "api_key_used must be false" in result["errors"]


def test_validator_rejects_safety_flag_private_endpoint_true(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest = _load_json(_config(tmp_path).manifest_path)
    manifest["private_endpoint_used"] = True
    _write_json(_config(tmp_path).manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "private_endpoint_used must be false" in result["errors"]


def test_validator_rejects_safety_flag_orders_true(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest = _load_json(_config(tmp_path).manifest_path)
    manifest["orders_enabled"] = True
    _write_json(_config(tmp_path).manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "orders_enabled must be false" in result["errors"]


def test_validator_rejects_safety_flag_paper_live_true(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest = _load_json(_config(tmp_path).manifest_path)
    manifest["paper_live_enabled"] = True
    _write_json(_config(tmp_path).manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "paper_live_enabled must be false" in result["errors"]


def test_validator_rejects_safety_flag_trading_true(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest = _load_json(_config(tmp_path).manifest_path)
    manifest["trading_enabled"] = True
    _write_json(_config(tmp_path).manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "trading_enabled must be false" in result["errors"]


def test_validator_rejects_safety_flag_ml_true(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest = _load_json(_config(tmp_path).manifest_path)
    manifest["ml_enabled"] = True
    _write_json(_config(tmp_path).manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "ml_enabled must be false" in result["errors"]


def test_validator_rejects_safety_flag_labels_true(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest = _load_json(_config(tmp_path).manifest_path)
    manifest["labels_enabled"] = True
    _write_json(_config(tmp_path).manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "labels_enabled must be false" in result["errors"]


def test_validator_rejects_safety_flag_backtest_true(tmp_path: Path) -> None:
    _prepare_valid_ingestion(tmp_path)
    manifest = _load_json(_config(tmp_path).manifest_path)
    manifest["backtest_enabled"] = True
    _write_json(_config(tmp_path).manifest_path, manifest)
    result = validate_public_market_ingestion_v2_3(tmp_path)
    assert result["passed"] is False
    assert "backtest_enabled must be false" in result["errors"]


def _prepare_valid_ingestion(tmp_path: Path) -> None:
    _write_raw_zip(tmp_path, minutes=1440)
    manifest = run_public_market_ingestion(_config(tmp_path))
    assert manifest["status"] == "PASS"


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


def _write_silver_and_sync_basic_manifest(tmp_path: Path, frame: pd.DataFrame) -> None:
    config = _config(tmp_path)
    write_parquet(frame, config.silver_path)
    manifest = _load_json(config.manifest_path)
    manifest["silver"]["sha256"] = sha256_file(config.silver_path)
    manifest["silver"]["bytes"] = config.silver_path.stat().st_size
    manifest["status"] = "PASS"
    _write_json(config.manifest_path, manifest)
    report = _load_json(config.quality_json_path)
    report["status"] = "PASS"
    _write_json(config.quality_json_path, report)


def _write_silver_and_sync_quality_manifest(tmp_path: Path, frame: pd.DataFrame) -> None:
    config = _config(tmp_path)
    write_parquet(frame, config.silver_path)
    manifest = _load_json(config.manifest_path)
    manifest["silver"]["sha256"] = sha256_file(config.silver_path)
    manifest["silver"]["bytes"] = config.silver_path.stat().st_size
    manifest["quality"] = assess_ohlcv_quality(frame, expected_rows=config.expected_rows, timeframe=config.timeframe).payload
    manifest["status"] = "PASS"
    _write_json(config.manifest_path, manifest)
    report = _load_json(config.quality_json_path)
    report["status"] = "PASS"
    report["quality"] = manifest["quality"]
    _write_json(config.quality_json_path, report)


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


def _rewrite_raw_zip_with_first_open(tmp_path: Path, open_value: str) -> None:
    config = _config(tmp_path)
    rows = _csv_rows(minutes=1440).splitlines()
    cells = rows[0].split(",")
    cells[1] = open_value
    rows[0] = ",".join(cells)
    with zipfile.ZipFile(config.raw_path, "w") as archive:
        archive.writestr("BTCUSDT-1m-2024-01-15.csv", "\n".join(rows) + "\n")


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
