from __future__ import annotations

import json
import zipfile
from copy import deepcopy
from pathlib import Path

import pandas as pd

from galapagos.data.public_trades.config import (
    DOC_PATH_V7_0,
    MANIFEST_PATH_V7_0,
    REPORT_JSON_PATH_V7_0,
    REPORT_MD_PATH_V7_0,
    SCHEMA_VERSION_V7_0,
)
from galapagos.data.public_trades.ingestion import normalize_agg_trades, safety_flags_v7_0
from galapagos.data.public_trades.provenance import sha256_file
from galapagos.data.public_trades.quality import assess_agg_trades_frame
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_0
from galapagos.data.public_trades.validation import validate_public_trades_v7_0


def test_validator_v7_0_accepts_valid_public_trades(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    result = validate_public_trades_v7_0(tmp_path)

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_v7_0_rejects_missing_raw_zip(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    paths["raw"].unlink()

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "missing raw zip")


def test_validator_v7_0_rejects_wrong_raw_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    manifest = _load_json(paths["manifest"])
    manifest["raw_files"]["2023-03-25"]["sha256"] = "0" * 64
    _write_manifest_and_report(paths, manifest)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "raw checksum mismatch")


def test_validator_v7_0_rejects_duplicate_aggregate_trade_id_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["output"], engine="pyarrow")
    frame.loc[1, "aggregate_trade_id"] = frame.loc[0, "aggregate_trade_id"]
    _sync_output(paths, frame)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "duplicate aggregate_trade_id")


def test_validator_v7_0_rejects_non_monotonic_aggregate_trade_id_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["output"], engine="pyarrow")
    frame.loc[1, "aggregate_trade_id"] = frame.loc[0, "aggregate_trade_id"] - 1
    _sync_output(paths, frame)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "aggregate_trade_id is not monotonic")


def test_validator_v7_0_rejects_non_positive_price_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["output"], engine="pyarrow")
    frame.loc[0, "price"] = 0.0
    _sync_output(paths, frame)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "non-positive price")


def test_validator_v7_0_rejects_non_positive_quantity_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["output"], engine="pyarrow")
    frame.loc[0, "quantity"] = 0.0
    _sync_output(paths, frame)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "non-positive quantity")


def test_validator_v7_0_rejects_extra_signal_column_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["output"], engine="pyarrow")
    frame["signal"] = "none"
    _sync_output(paths, frame)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "schema mismatch")


def test_validator_v7_0_rejects_extra_order_column_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["output"], engine="pyarrow")
    frame["order"] = "none"
    _sync_output(paths, frame)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "schema mismatch")


def test_validator_v7_0_rejects_extra_pnl_column_even_with_synced_checksum(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    frame = pd.read_parquet(paths["output"], engine="pyarrow")
    frame["pnl"] = 0.0
    _sync_output(paths, frame)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "schema mismatch")


def test_validator_v7_0_rejects_report_json_lie(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    report = _load_json(paths["report"])
    report["outputs"]["rows"] = 999
    paths["report"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "report JSON")


def test_validator_v7_0_rejects_manifest_unexpected_key(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    manifest = _load_json(paths["manifest"])
    manifest["unexpected"] = True
    _write_manifest_and_report(paths, manifest)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "unexpected keys")


def test_validator_v7_0_rejects_report_unexpected_key(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    report = _load_json(paths["report"])
    report["unexpected"] = True
    paths["report"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "report JSON")


def test_validator_v7_0_rejects_markdown_strategy_validated_claim(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    paths["report_md"].write_text("strategy validated\n", encoding="utf-8")

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "forbidden claim")


def test_validator_v7_0_rejects_safety_flag_trading_true(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    manifest = _load_json(paths["manifest"])
    manifest["safety"]["trading_enabled"] = True
    _write_manifest_and_report(paths, manifest)

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "safety flag must be false: trading_enabled")


def test_validator_v7_0_rejects_features_v7_0_directory_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    forbidden = tmp_path / "data/research/v7_0/features/feature.parquet"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("x", encoding="utf-8")

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "Forbidden V7.0 artifact detected")


def test_validator_v7_0_rejects_labels_v7_0_directory_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    forbidden = tmp_path / "data/research/v7_0/labels/labels.parquet"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("x", encoding="utf-8")

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "Forbidden V7.0 artifact detected")


def test_validator_v7_0_rejects_dataset_ml_v7_0_directory_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    forbidden = tmp_path / "data/research/v7_0/datasets/dataset.parquet"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("x", encoding="utf-8")

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "Forbidden V7.0 artifact detected")


def test_validator_v7_0_rejects_backtest_report_created(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    forbidden = tmp_path / "reports/backtests/backtest.json"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("{}", encoding="utf-8")

    result = validate_public_trades_v7_0(tmp_path)

    assert _contains(result["errors"], "Forbidden V7.0 artifact detected")


def _write_fixture(root: Path) -> dict[str, Path]:
    raw = root / "data/raw/public_trades/binance_archive/spot/BTCUSDT/aggTrades/BTCUSDT-aggTrades-2023-03-25.zip"
    raw.parent.mkdir(parents=True)
    csv = "\n".join(
        [
            "1,27000.0,0.10,10,10,1679702400000,true,true",
            "2,27001.0,0.20,11,12,1679702401000,false,true",
            "3,27002.0,0.30,13,13,1679702402000,true,true",
        ]
    )
    with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("BTCUSDT-aggTrades-2023-03-25.csv", csv)
    raw_sha = sha256_file(raw)
    raw_frame = pd.DataFrame(
        {
            "aggregate_trade_id": [1, 2, 3],
            "price": [27000.0, 27001.0, 27002.0],
            "quantity": [0.10, 0.20, 0.30],
            "first_trade_id": [10, 11, 13],
            "last_trade_id": [10, 12, 13],
            "trade_time": [1679702400000, 1679702401000, 1679702402000],
            "is_buyer_maker": [True, False, True],
            "is_best_match": [True, True, True],
        }
    )
    frame = normalize_agg_trades(raw_frame, raw_sha=raw_sha, ingestion_run_id="v7_0_test")
    output = root / "data/research/v7_0/trades/aggTrades/source=binance_archive/market_type=spot/symbol=BTCUSDT/window=2023-03-25_2023-03-25/agg_trades.parquet"
    _write_parquet(frame, output)
    manifest = _manifest_payload(root, raw, output, frame)
    paths = {
        "raw": raw,
        "output": output,
        "manifest": root / MANIFEST_PATH_V7_0,
        "report": root / REPORT_JSON_PATH_V7_0,
        "report_md": root / REPORT_MD_PATH_V7_0,
        "doc": root / DOC_PATH_V7_0,
    }
    _write_manifest_and_report(paths, manifest)
    paths["report_md"].parent.mkdir(parents=True, exist_ok=True)
    paths["report_md"].write_text("V7.0 ne valide aucune strategie.\n", encoding="utf-8")
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text("V7.0 ne produit aucun backtest.\n", encoding="utf-8")
    return paths


def _manifest_payload(root: Path, raw: Path, output: Path, frame: pd.DataFrame) -> dict:
    quality = assess_agg_trades_frame(frame, expected_rows=len(frame))
    return {
        "version": "V7.0",
        "status": "PASS",
        "created_at_utc": "2026-05-25T00:00:00Z",
        "ingestion_run_id": "v7_0_test",
        "source": {
            "name": "binance_public_archive",
            "venue": "binance",
            "market_type": "spot",
            "symbol": "BTCUSDT",
            "trade_source_type": "aggTrades",
        },
        "discovery": {
            "first_available_date": "2023-03-25",
            "last_available_date": "2023-03-25",
            "window_start": "2023-03-25",
            "window_end": "2023-03-25",
            "total_days": 1,
            "matches_v5_0_window": False,
            "v5_0_window_start": "2023-03-25",
            "v5_0_window_end": "2026-05-23",
            "missing_dates": [],
            "documented_gaps_allowed": False,
            "window_selection_reason": "bounded test fixture",
        },
        "raw_files": {
            "2023-03-25": {
                "path": raw.relative_to(root).as_posix(),
                "sha256": sha256_file(raw),
                "bytes": raw.stat().st_size,
                "rows": 3,
            }
        },
        "outputs": {
            "path": output.relative_to(root).as_posix(),
            "sha256": sha256_file(output),
            "bytes": output.stat().st_size,
            "rows": len(frame),
            "format": "parquet",
        },
        "schema_version": SCHEMA_VERSION_V7_0,
        "trade_columns": AGG_TRADE_COLUMNS_V7_0,
        "quality": quality,
        "safety": safety_flags_v7_0(),
        "limitations": [
            "V7.0 ingere uniquement des trades publics historiques en lecture seule.",
            "V7.0 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
        ],
    }


def _sync_output(paths: dict[str, Path], frame: pd.DataFrame) -> None:
    _write_parquet(frame, paths["output"])
    manifest = _load_json(paths["manifest"])
    manifest["outputs"]["sha256"] = sha256_file(paths["output"])
    manifest["outputs"]["bytes"] = paths["output"].stat().st_size
    manifest["outputs"]["rows"] = len(frame)
    _write_manifest_and_report(paths, manifest)


def _write_manifest_and_report(paths: dict[str, Path], manifest: dict) -> None:
    paths["manifest"].parent.mkdir(parents=True, exist_ok=True)
    paths["manifest"].write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["report"].parent.mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(deepcopy(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False, engine="pyarrow")


def _contains(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)
