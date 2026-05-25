from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from galapagos.data.public_trades.config import MANIFEST_PATH_V7_0
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_0, FORBIDDEN_TRADE_COLUMNS_V7_0


ROOT = Path(__file__).resolve().parents[2]


def _manifest() -> dict:
    return json.loads((ROOT / MANIFEST_PATH_V7_0).read_text(encoding="utf-8"))


def _frame() -> pd.DataFrame:
    manifest = _manifest()
    return pd.read_parquet(ROOT / manifest["outputs"]["path"], engine="pyarrow")


def test_public_trades_discovery_has_window() -> None:
    discovery = _manifest()["discovery"]

    assert discovery["window_start"] <= discovery["window_end"]
    assert discovery["total_days"] >= 1
    assert discovery["documented_gaps_allowed"] is False


def test_public_trades_schema_strict() -> None:
    frame = _frame()

    assert list(frame.columns) == AGG_TRADE_COLUMNS_V7_0


def test_public_trades_price_quantity_positive() -> None:
    frame = _frame()

    assert (frame["price"] > 0).all()
    assert (frame["quantity"] > 0).all()


def test_public_trades_trade_ids_monotonic() -> None:
    frame = _frame()

    assert frame["aggregate_trade_id"].is_monotonic_increasing
    assert (frame["first_trade_id"] <= frame["last_trade_id"]).all()


def test_public_trades_no_duplicate_aggregate_trade_ids() -> None:
    frame = _frame()

    assert int(frame["aggregate_trade_id"].duplicated().sum()) == 0


def test_public_trades_timestamps_utc() -> None:
    frame = _frame()

    assert "UTC" in str(frame["event_ts"].dtype)
    assert "UTC" in str(frame["trade_ts"].dtype)
    assert (frame["available_ts"] >= frame["trade_ts"]).all()
    assert (frame["decision_ts"] >= frame["available_ts"]).all()


def test_public_trades_no_forbidden_columns() -> None:
    frame = _frame()
    forbidden = [column for column in frame.columns if column.casefold() in FORBIDDEN_TRADE_COLUMNS_V7_0]

    assert forbidden == []
