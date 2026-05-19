from __future__ import annotations

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


@pytest.fixture(scope="session")
def valid_v2_4_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("valid_v2_4_template")
    _prepare_valid_resampling(root)
    return root


@pytest.fixture()
def tmp_path(tmp_path_factory: pytest.TempPathFactory, valid_v2_4_template: Path) -> Path:
    destination = tmp_path_factory.mktemp("valid_v2_4_project")
    shutil.copytree(valid_v2_4_template, destination, dirs_exist_ok=True)
    _sync_copied_ingestion_manifest(destination)
    return destination


def test_validator_v2_4_accepts_valid_resampling(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is True
    assert result["manifest"]["outputs"]["5m"]["rows"] == 288
    assert result["manifest"]["outputs"]["15m"]["rows"] == 96
    assert result["manifest"]["outputs"]["1h"]["rows"] == 24


def test_validator_v2_4_rejects_modified_5m_high_even_with_synced_checksum(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    frame = read_parquet(resampled_silver_path(tmp_path, "5m"))
    frame.loc[0, "high"] = frame.loc[0, "high"] + 100
    _write_output_and_sync_manifest(tmp_path, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("5m parent-child mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_modified_15m_volume_even_with_synced_checksum(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    frame = read_parquet(resampled_silver_path(tmp_path, "15m"))
    frame.loc[0, "volume"] = frame.loc[0, "volume"] + 1
    _write_output_and_sync_manifest(tmp_path, "15m", frame)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("15m parent-child mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_modified_1h_close_even_with_synced_checksum(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    frame = read_parquet(resampled_silver_path(tmp_path, "1h"))
    frame.loc[0, "close"] = frame.loc[0, "close"] + 1
    _write_output_and_sync_manifest(tmp_path, "1h", frame)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("1h parent-child mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_deleted_resampled_row_even_with_synced_checksum(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    frame = read_parquet(resampled_silver_path(tmp_path, "5m")).drop(index=1).reset_index(drop=True)
    _write_output_and_sync_manifest(tmp_path, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("5m row count mismatch" in error or "5m rows mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_shuffled_resampled_parquet_even_with_synced_checksum(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    frame = read_parquet(resampled_silver_path(tmp_path, "5m")).sample(frac=1.0, random_state=11).reset_index(drop=True)
    _write_output_and_sync_manifest(tmp_path, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("5m physical event_ts is not monotonic" in error for error in result["errors"])


def test_validator_v2_4_rejects_wrong_expected_rows(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["expected_rows"]["5m"] = 999
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "expected rows mismatch for 5m" in result["errors"]


def test_validator_v2_4_rejects_wrong_raw_file_sha256_in_resampled_silver(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    frame = read_parquet(resampled_silver_path(tmp_path, "5m"))
    frame.loc[:, "raw_file_sha256"] = "wrong"
    _write_output_and_sync_manifest(tmp_path, "5m", frame)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("5m provenance raw_file_sha256 mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_wrong_ingestion_run_id_in_resampled_silver(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    frame = read_parquet(resampled_silver_path(tmp_path, "15m"))
    frame.loc[:, "ingestion_run_id"] = "wrong"
    _write_output_and_sync_manifest(tmp_path, "15m", frame)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("15m provenance ingestion_run_id mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_safety_flag_trading_true(tmp_path: Path) -> None:
    _assert_safety_flag_rejected(tmp_path, "trading_enabled", "trading_enabled must be false")


def test_validator_v2_4_rejects_safety_flag_ml_true(tmp_path: Path) -> None:
    _assert_safety_flag_rejected(tmp_path, "ml_enabled", "ml_enabled must be false")


def test_validator_v2_4_rejects_safety_flag_labels_true(tmp_path: Path) -> None:
    _assert_safety_flag_rejected(tmp_path, "labels_enabled", "labels_enabled must be false")


def test_validator_v2_4_rejects_safety_flag_backtest_true(tmp_path: Path) -> None:
    _assert_safety_flag_rejected(tmp_path, "backtest_enabled", "backtest_enabled must be false")


def test_validator_v2_4_rejects_safety_flag_orders_true(tmp_path: Path) -> None:
    _assert_safety_flag_rejected(tmp_path, "orders_enabled", "orders_enabled must be false")


def test_validator_v2_4_rejects_manifest_quality_rows_lie_even_if_report_synced(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    _set_manifest_and_report_quality_field(tmp_path, "5m", "rows", 123)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "V2.4 manifest quality mismatch for 5m.rows" in result["errors"]


def test_validator_v2_4_rejects_manifest_quality_gap_count_lie_even_if_report_synced(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    _set_manifest_and_report_quality_field(tmp_path, "15m", "gap_count", 99)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "V2.4 manifest quality mismatch for 15m.gap_count" in result["errors"]


def test_validator_v2_4_rejects_manifest_quality_monotonic_lie_even_if_report_synced(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    _set_manifest_and_report_quality_field(tmp_path, "1h", "monotonic_event_ts", False)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "V2.4 manifest quality mismatch for 1h.monotonic_event_ts" in result["errors"]


def test_validator_v2_4_rejects_quality_report_output_checksum_lie(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["outputs"]["5m"]["sha256"] = "bad"
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "quality report outputs mismatch" in result["errors"]


def test_validator_v2_4_rejects_quality_report_input_sha_lie(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["input_1m"]["sha256"] = "bad"
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "quality report input_1m mismatch" in result["errors"]


def test_validator_v2_4_rejects_quality_report_expected_rows_lie(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["expected_rows"]["5m"] = 999
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "quality report expected_rows mismatch" in result["errors"]


def test_validator_v2_4_rejects_quality_report_parent_child_lie(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["parent_child_consistency"] = False
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "quality report parent_child_consistency mismatch" in result["errors"]


def test_validator_v2_4_rejects_quality_report_resampling_run_id_lie(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["resampling_run_id"] = "wrong"
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "quality report resampling_run_id mismatch" in result["errors"]


def test_validator_v2_4_rejects_quality_report_created_at_lie(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["created_at_utc"] = "1970-01-01T00:00:00Z"
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "quality report created_at_utc mismatch" in result["errors"]


def test_validator_v2_4_rejects_quality_report_limitations_lie(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["limitations"] = []
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "quality report limitations mismatch" in result["errors"]


def test_validator_v2_4_rejects_quality_report_unexpected_top_level_key(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["claim"] = "strategy validated"
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("quality report unexpected keys" in error for error in result["errors"])


def test_validator_v2_4_rejects_quality_report_top_level_trading_enabled_true(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["trading_enabled"] = True
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("quality report unexpected keys" in error for error in result["errors"])


def test_validator_v2_4_rejects_manifest_unexpected_top_level_key(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["strategy_validated"] = True
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["strategy_validated"] = True
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("V2.4 manifest unexpected keys" in error for error in result["errors"])


def test_validator_v2_4_rejects_manifest_unexpected_execution_key(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["execution_enabled"] = True
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("V2.4 manifest unexpected keys" in error for error in result["errors"])


def test_validator_v2_4_rejects_output_unexpected_key(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["outputs"]["5m"]["claim"] = "ok"
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["outputs"]["5m"]["claim"] = "ok"
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("V2.4 manifest outputs.5m unexpected keys" in error for error in result["errors"])


def test_validator_v2_4_rejects_quality_unexpected_key(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["quality"]["5m"]["claim"] = "ok"
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["quality"]["5m"]["claim"] = "ok"
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("V2.4 manifest quality.5m unexpected keys" in error for error in result["errors"])


def test_validator_v2_4_rejects_report_safety_unexpected_key(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["safety"]["execution_enabled"] = True
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("quality report safety unexpected keys" in error for error in result["errors"])


def test_validator_v2_4_rejects_markdown_forbidden_strategy_claim(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    markdown_path = tmp_path / "reports/data_quality/ohlcv_resampling_v2_4.md"
    markdown_path.write_text(markdown_path.read_text(encoding="utf-8") + "\nStrategy validated.\n", encoding="utf-8")
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "quality markdown contains forbidden claim: strategy validated" in result["errors"]


def test_validator_v2_4_allows_markdown_negative_safety_claims(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    markdown_path = tmp_path / "reports/data_quality/ohlcv_resampling_v2_4.md"
    markdown_path.write_text(
        markdown_path.read_text(encoding="utf-8")
        + "\nAucun trading. V2.4 ne valide aucune stratégie. Aucun ordre.\n",
        encoding="utf-8",
    )
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is True


def test_validator_v2_4_rejects_synced_limitations_strategy_validated_claim(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["limitations"].append("strategy validated")
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["limitations"].append("strategy validated")
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("forbidden claim" in error or "V2.4 manifest limitations mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_synced_limitations_trading_enabled_claim(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["limitations"].append("trading enabled")
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["limitations"].append("trading enabled")
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any("forbidden claim" in error or "V2.4 manifest limitations mismatch" in error for error in result["errors"])


def test_validator_v2_4_rejects_empty_synced_limitations(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["limitations"] = []
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["limitations"] = []
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert any(
        error in {"V2.4 manifest limitations mismatch", "quality report limitations mismatch"}
        for error in result["errors"]
    )


def test_validator_v2_4_rejects_invalid_created_at_even_if_report_synced(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["created_at_utc"] = "not-a-date"
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["created_at_utc"] = "not-a-date"
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "V2.4 manifest created_at_utc invalid" in result["errors"]


def test_validator_v2_4_rejects_invalid_resampling_run_id_even_if_report_synced(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    manifest["resampling_run_id"] = "bogus"
    _write_json(tmp_path / MANIFEST_PATH, manifest)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    report["resampling_run_id"] = "bogus"
    _write_json(tmp_path / QUALITY_JSON_PATH, report)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is False
    assert "V2.4 manifest resampling_run_id invalid" in result["errors"]


def test_validator_v2_4_allows_expected_limitations(tmp_path: Path) -> None:
    _prepare_valid_resampling(tmp_path)
    manifest = _load_json(tmp_path / MANIFEST_PATH)
    report = _load_json(tmp_path / QUALITY_JSON_PATH)
    result = validate_ohlcv_resampling_v2_4(tmp_path)
    assert result["passed"] is True
    assert manifest["limitations"] == EXPECTED_LIMITATIONS_V2_4
    assert report["limitations"] == EXPECTED_LIMITATIONS_V2_4


def _assert_safety_flag_rejected(tmp_path: Path, field: str, expected_error: str) -> None:
    _prepare_valid_resampling(tmp_path)
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
