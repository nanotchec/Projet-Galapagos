from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from galapagos.data.public_trades.config import MANIFEST_PATH_V8_2
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V8_2, FORBIDDEN_TRADE_COLUMNS_V8_2


ROOT = Path(__file__).resolve().parents[2]


def _manifest() -> dict:
    return json.loads((ROOT / MANIFEST_PATH_V8_2).read_text(encoding="utf-8"))


def _partition_frames():
    manifest = _manifest()
    partitions = sorted(manifest["outputs"]["partitions"].items())
    selected = [partitions[0], partitions[len(partitions) // 2], partitions[-1]]
    for date_key, payload in selected:
        yield date_key, pd.read_parquet(ROOT / payload["path"], engine="pyarrow")


def test_public_trades_v8_2_window_has_366_days() -> None:
    discovery = _manifest()["discovery"]

    assert discovery["window_start"] == "2023-03-25"
    assert discovery["window_end"] == "2024-03-24"
    assert discovery["total_days"] == 366
    assert discovery["documented_gaps_allowed"] is False


def test_public_trades_v8_2_schema_strict() -> None:
    for _date_key, frame in _partition_frames():
        assert list(frame.columns) == AGG_TRADE_COLUMNS_V8_2


def test_public_trades_v8_2_price_quantity_positive() -> None:
    for _date_key, frame in _partition_frames():
        assert (frame["price"] > 0).all()
        assert (frame["quantity"] > 0).all()


def test_public_trades_v8_2_trade_ids_monotonic() -> None:
    manifest = _manifest()

    assert manifest["quality"]["non_monotonic_trade_ids"] == 0
    assert manifest["quality"]["trade_id_range_violations"] == 0
    for _date_key, frame in _partition_frames():
        assert frame["aggregate_trade_id"].is_monotonic_increasing
        assert (frame["first_trade_id"] <= frame["last_trade_id"]).all()


def test_public_trades_v8_2_no_duplicate_aggregate_trade_ids() -> None:
    manifest = _manifest()

    assert manifest["quality"]["duplicate_aggregate_trade_ids"] == 0
    for _date_key, frame in _partition_frames():
        assert int(frame["aggregate_trade_id"].duplicated().sum()) == 0


def test_public_trades_v8_2_timestamps_utc() -> None:
    manifest = _manifest()

    assert manifest["quality"]["timestamps_utc"] is True
    assert manifest["quality"]["timestamp_order_valid"] is True
    assert manifest["quality"]["non_monotonic_event_ts"] == 0
    for _date_key, frame in _partition_frames():
        assert "UTC" in str(frame["event_ts"].dtype)
        assert "UTC" in str(frame["trade_ts"].dtype)
        assert (frame["available_ts"] >= frame["trade_ts"]).all()
        assert (frame["decision_ts"] >= frame["available_ts"]).all()


def test_public_trades_v8_2_no_forbidden_columns() -> None:
    for _date_key, frame in _partition_frames():
        forbidden = [column for column in frame.columns if column.casefold() in FORBIDDEN_TRADE_COLUMNS_V8_2]
        assert forbidden == []
