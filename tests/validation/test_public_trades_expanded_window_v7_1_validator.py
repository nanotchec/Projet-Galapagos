from __future__ import annotations

import json
import zipfile
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from galapagos.data.public_trades.config import (
    DOC_PATH_V7_1,
    MANIFEST_PATH_V7_1,
    REPORT_JSON_PATH_V7_1,
    REPORT_MD_PATH_V7_1,
    SCHEMA_VERSION_V7_1,
    output_partition_path_v7_1,
    raw_zip_path,
)
from galapagos.data.public_trades.expanded_window import safety_flags_v7_1
from galapagos.data.public_trades.expanded_window_quality import assess_expanded_agg_trade_partitions_v7_1
from galapagos.data.public_trades.expanded_window_validation import validate_public_trades_expanded_window_v7_1
from galapagos.data.public_trades.ingestion import normalize_agg_trades
from galapagos.data.public_trades.provenance import sha256_file
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_1


def test_validator_v7_1_accepts_valid_public_trades(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v7_1_rejects_missing_raw_zip(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    paths["raw_by_date"]["2023-03-25"].unlink()

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "missing raw zip")


def test_validator_v7_1_rejects_wrong_raw_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    manifest = _load_json(paths["manifest"])
    manifest["raw_files"]["2023-03-25"]["sha256"] = "0" * 64
    _write_manifest_and_report(paths, manifest)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "raw checksum mismatch")


def test_validator_v7_1_rejects_duplicate_aggregate_trade_id_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["partition_by_date"]["2023-03-25"], engine="pyarrow")
    frame.loc[1, "aggregate_trade_id"] = frame.loc[0, "aggregate_trade_id"]
    _sync_partition(paths, "2023-03-25", frame)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "duplicate aggregate_trade_id")


def test_validator_v7_1_rejects_non_monotonic_aggregate_trade_id_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["partition_by_date"]["2023-03-25"], engine="pyarrow")
    frame.loc[1, "aggregate_trade_id"] = frame.loc[0, "aggregate_trade_id"] - 1
    _sync_partition(paths, "2023-03-25", frame)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "aggregate_trade_id is not monotonic")


def test_validator_v7_1_rejects_non_positive_price_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["partition_by_date"]["2023-03-25"], engine="pyarrow")
    frame.loc[0, "price"] = 0.0
    _sync_partition(paths, "2023-03-25", frame)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "non-positive price")


def test_validator_v7_1_rejects_non_positive_quantity_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["partition_by_date"]["2023-03-25"], engine="pyarrow")
    frame.loc[0, "quantity"] = 0.0
    _sync_partition(paths, "2023-03-25", frame)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "non-positive quantity")


def test_validator_v7_1_rejects_extra_signal_column_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["partition_by_date"]["2023-03-25"], engine="pyarrow")
    frame["signal"] = "none"
    _sync_partition(paths, "2023-03-25", frame)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "schema mismatch")


def test_validator_v7_1_rejects_extra_order_column_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["partition_by_date"]["2023-03-25"], engine="pyarrow")
    frame["order"] = "none"
    _sync_partition(paths, "2023-03-25", frame)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "schema mismatch")


def test_validator_v7_1_rejects_extra_pnl_column_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["partition_by_date"]["2023-03-25"], engine="pyarrow")
    frame["pnl"] = 0.0
    _sync_partition(paths, "2023-03-25", frame)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "schema mismatch")


def test_validator_v7_1_rejects_report_json_lie(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    report = _load_json(paths["report"])
    report["outputs"]["total_rows"] = 999
    paths["report"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "report JSON")


def test_validator_v7_1_rejects_manifest_unexpected_key(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    manifest = _load_json(paths["manifest"])
    manifest["unexpected"] = True
    _write_manifest_and_report(paths, manifest)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "unexpected keys")


def test_validator_v7_1_rejects_report_unexpected_key(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    report = _load_json(paths["report"])
    report["unexpected"] = True
    paths["report"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "report JSON")


def test_validator_v7_1_rejects_markdown_strategy_validated_claim(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    paths["report_md"].write_text("strategy validated\n", encoding="utf-8")

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "forbidden claim")


def test_validator_v7_1_rejects_safety_flag_trading_true(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    manifest = _load_json(paths["manifest"])
    manifest["safety"]["trading_enabled"] = True
    _write_manifest_and_report(paths, manifest)

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "safety flag must be false: trading_enabled")


def test_validator_v7_1_rejects_features_v7_1_directory_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    forbidden = tmp_path / "data/research/v7_1/features/feature.parquet"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("x", encoding="utf-8")

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "Forbidden V7.1 artifact detected")


def test_validator_v7_1_rejects_labels_v7_1_directory_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    forbidden = tmp_path / "data/research/v7_1/labels/labels.parquet"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("x", encoding="utf-8")

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "Forbidden V7.1 artifact detected")


def test_validator_v7_1_rejects_dataset_ml_v7_1_directory_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    forbidden = tmp_path / "data/research/v7_1/datasets/dataset.parquet"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("x", encoding="utf-8")

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "Forbidden V7.1 artifact detected")


def test_validator_v7_1_rejects_backtest_report_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    forbidden = tmp_path / "reports/backtests/backtest.json"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("{}", encoding="utf-8")

    result = validate_public_trades_expanded_window_v7_1(tmp_path)

    assert _contains(result["errors"], "Forbidden V7.1 artifact detected")


def _write_fixture(root: Path) -> dict:
    raw_by_date: dict[str, Path] = {}
    partition_by_date: dict[str, Path] = {}
    raw_files: dict[str, dict] = {}
    partitions: dict[str, dict] = {}
    ingestion_run_id = "v7_1_test"
    base_trade_time = 1679702400000
    for offset, date_key in enumerate(_dates()):
        raw = raw_zip_path(root, date_key)
        raw.parent.mkdir(parents=True, exist_ok=True)
        first_id = offset * 10 + 1
        first_trade_time = base_trade_time + offset * 86_400_000
        csv = "\n".join(
            [
                f"{first_id},27000.0,0.10,{first_id * 10},{first_id * 10},{first_trade_time},true,true",
                f"{first_id + 1},27001.0,0.20,{first_id * 10 + 1},{first_id * 10 + 2},{first_trade_time + 1000},false,true",
                f"{first_id + 2},27002.0,0.30,{first_id * 10 + 3},{first_id * 10 + 3},{first_trade_time + 2000},true,true",
            ]
        )
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(f"BTCUSDT-aggTrades-{date_key}.csv", csv)
        raw_sha = sha256_file(raw)
        raw_frame = pd.DataFrame(
            {
                "aggregate_trade_id": [first_id, first_id + 1, first_id + 2],
                "price": [27000.0, 27001.0, 27002.0],
                "quantity": [0.10, 0.20, 0.30],
                "first_trade_id": [first_id * 10, first_id * 10 + 1, first_id * 10 + 3],
                "last_trade_id": [first_id * 10, first_id * 10 + 2, first_id * 10 + 3],
                "trade_time": [first_trade_time, first_trade_time + 1000, first_trade_time + 2000],
                "is_buyer_maker": [True, False, True],
                "is_best_match": [True, True, True],
            }
        )
        frame = normalize_agg_trades(
            raw_frame,
            raw_sha=raw_sha,
            ingestion_run_id=ingestion_run_id,
            schema_version=SCHEMA_VERSION_V7_1,
            columns=AGG_TRADE_COLUMNS_V7_1,
        )
        output = output_partition_path_v7_1(root, "2023-03-25", "2023-04-23", date_key)
        _write_parquet(frame, output)
        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        raw_files[date_key] = {
            "path": raw.relative_to(root).as_posix(),
            "sha256": raw_sha,
            "bytes": raw.stat().st_size,
            "rows": 3,
        }
        partitions[date_key] = {
            "path": output.relative_to(root).as_posix(),
            "sha256": sha256_file(output),
            "bytes": output.stat().st_size,
            "rows": len(frame),
            "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z"),
            "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z"),
            "raw_file_sha256": raw_sha,
        }
        raw_by_date[date_key] = raw
        partition_by_date[date_key] = output
    manifest = _manifest_payload(root, raw_files, partitions)
    paths = {
        "raw_by_date": raw_by_date,
        "partition_by_date": partition_by_date,
        "manifest": root / MANIFEST_PATH_V7_1,
        "report": root / REPORT_JSON_PATH_V7_1,
        "report_md": root / REPORT_MD_PATH_V7_1,
        "doc": root / DOC_PATH_V7_1,
    }
    _write_manifest_and_report(paths, manifest)
    paths["report_md"].parent.mkdir(parents=True, exist_ok=True)
    paths["report_md"].write_text("V7.1 ne valide aucune strategie.\n", encoding="utf-8")
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text("V7.1 ne produit aucun backtest.\n", encoding="utf-8")
    return paths


def _manifest_payload(root: Path, raw_files: dict[str, dict], partitions: dict[str, dict]) -> dict:
    total_rows = sum(item["rows"] for item in partitions.values())
    total_bytes = sum(item["bytes"] for item in partitions.values())
    quality = assess_expanded_agg_trade_partitions_v7_1(root, partitions, expected_days=30, missing_dates=[])
    return {
        "version": "V7.1",
        "status": "PASS",
        "created_at_utc": "2026-05-25T00:00:00Z",
        "ingestion_run_id": "v7_1_test",
        "source": {
            "name": "binance_public_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "trade_source_type": "aggTrades",
        },
        "discovery": {
            "window_start": "2023-03-25",
            "window_end": "2023-04-23",
            "total_days": 30,
            "matches_v5_0_window": False,
            "v5_0_window_start": "2023-03-25",
            "v5_0_window_end": "2026-05-23",
            "missing_dates": [],
            "documented_gaps_allowed": False,
            "window_selection_reason": "bounded test fixture",
        },
        "raw_files": raw_files,
        "outputs": {
            "partitions": partitions,
            "total_rows": total_rows,
            "total_bytes": total_bytes,
            "format": "partitioned_parquet",
        },
        "schema_version": SCHEMA_VERSION_V7_1,
        "trade_columns": AGG_TRADE_COLUMNS_V7_1,
        "quality": quality,
        "safety": safety_flags_v7_1(),
        "limitations": [
            "V7.1 etend uniquement l'ingestion de trades publics aggTrades sur une fenetre bornee de 30 jours.",
            "V7.1 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
        ],
    }


def _sync_partition(paths: dict, date_key: str, frame: pd.DataFrame) -> None:
    partition = paths["partition_by_date"][date_key]
    _write_parquet(frame, partition)
    manifest = _load_json(paths["manifest"])
    payload = manifest["outputs"]["partitions"][date_key]
    payload["sha256"] = sha256_file(partition)
    payload["bytes"] = partition.stat().st_size
    payload["rows"] = len(frame)
    manifest["outputs"]["total_rows"] = sum(item["rows"] for item in manifest["outputs"]["partitions"].values())
    manifest["outputs"]["total_bytes"] = sum(item["bytes"] for item in manifest["outputs"]["partitions"].values())
    _write_manifest_and_report(paths, manifest)


def _write_manifest_and_report(paths: dict, manifest: dict) -> None:
    paths["manifest"].parent.mkdir(parents=True, exist_ok=True)
    paths["manifest"].write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["report"].parent.mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(deepcopy(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _dates() -> list[str]:
    start = date.fromisoformat("2023-03-25")
    return [(start + timedelta(days=offset)).isoformat() for offset in range(30)]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False, engine="pyarrow")


def _contains(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
