from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from galapagos.data.public_trades.config import MANIFEST_PATH_V7_7
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_7, FORBIDDEN_TRADE_COLUMNS_V7_7


ROOT = Path(__file__).resolve().parents[2]


def _manifest() -> dict:
    return json.loads((ROOT / MANIFEST_PATH_V7_7).read_text(encoding="utf-8"))


def _partition_frames():
    manifest = _manifest()
    for date_key, payload in sorted(manifest["outputs"]["partitions"].items()):
        yield date_key, pd.read_parquet(ROOT / payload["path"], engine="pyarrow")


def test_public_trades_v7_7_window_has_90_days() -> None:
    discovery = _manifest()["discovery"]

    assert discovery["window_start"] == "2023-03-25"
    assert discovery["window_end"] == "2023-06-22"
    assert discovery["total_days"] == 90
    assert discovery["documented_gaps_allowed"] is False


def test_public_trades_v7_7_schema_strict() -> None:
    for _date_key, frame in _partition_frames():
        assert list(frame.columns) == AGG_TRADE_COLUMNS_V7_7


def test_public_trades_v7_7_price_quantity_positive() -> None:
    for _date_key, frame in _partition_frames():
        assert (frame["price"] > 0).all()
        assert (frame["quantity"] > 0).all()


def test_public_trades_v7_7_trade_ids_monotonic() -> None:
    previous_last_id = None
    for _date_key, frame in _partition_frames():
        assert frame["aggregate_trade_id"].is_monotonic_increasing
        assert (frame["first_trade_id"] <= frame["last_trade_id"]).all()
        first_id = int(frame["aggregate_trade_id"].iloc[0])
        if previous_last_id is not None:
            assert first_id > previous_last_id
        previous_last_id = int(frame["aggregate_trade_id"].iloc[-1])


def test_public_trades_v7_7_no_duplicate_aggregate_trade_ids() -> None:
    previous_last_id = None
    for _date_key, frame in _partition_frames():
        assert int(frame["aggregate_trade_id"].duplicated().sum()) == 0
        first_id = int(frame["aggregate_trade_id"].iloc[0])
        if previous_last_id is not None:
            assert first_id != previous_last_id
        previous_last_id = int(frame["aggregate_trade_id"].iloc[-1])


def test_public_trades_v7_7_timestamps_utc() -> None:
    previous_max_event_ts = None
    for _date_key, frame in _partition_frames():
        assert "UTC" in str(frame["event_ts"].dtype)
        assert "UTC" in str(frame["trade_ts"].dtype)
        assert (frame["available_ts"] >= frame["trade_ts"]).all()
        assert (frame["decision_ts"] >= frame["available_ts"]).all()
        min_event_ts = pd.to_datetime(frame["event_ts"], utc=True).min()
        if previous_max_event_ts is not None:
            assert min_event_ts >= previous_max_event_ts
        previous_max_event_ts = pd.to_datetime(frame["event_ts"], utc=True).max()


def test_public_trades_v7_7_no_forbidden_columns() -> None:
    for _date_key, frame in _partition_frames():
        forbidden = [column for column in frame.columns if column.casefold() in FORBIDDEN_TRADE_COLUMNS_V7_7]
        assert forbidden == []
