from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V7_0, FORBIDDEN_TRADE_COLUMNS_V7_0


def assess_agg_trades_frame(frame: pd.DataFrame, *, expected_rows: int | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    columns = list(frame.columns)
    forbidden = [column for column in columns if column.casefold() in FORBIDDEN_TRADE_COLUMNS_V7_0]
    if columns != AGG_TRADE_COLUMNS_V7_0:
        errors.append("AGG_TRADE_COLUMNS_V7_0 schema mismatch")
    if forbidden:
        errors.append(f"forbidden columns present: {forbidden}")
    if expected_rows is not None and len(frame) != expected_rows:
        errors.append(f"row count mismatch: {len(frame)} != {expected_rows}")

    duplicate_ids = int(frame["aggregate_trade_id"].duplicated().sum()) if "aggregate_trade_id" in frame else 0
    if duplicate_ids:
        errors.append("duplicate aggregate_trade_id rows detected")
    non_monotonic_trade_ids = _non_monotonic_count(frame["aggregate_trade_id"]) if "aggregate_trade_id" in frame else 0
    if non_monotonic_trade_ids:
        errors.append("aggregate_trade_id is not monotonic non-decreasing")
    non_monotonic_event_ts = _non_monotonic_count(pd.to_datetime(frame["event_ts"], utc=True)) if "event_ts" in frame else 0
    if non_monotonic_event_ts:
        errors.append("event_ts is not monotonic non-decreasing")

    price_non_positive = int((pd.to_numeric(frame["price"], errors="coerce") <= 0).sum()) if "price" in frame else 0
    quantity_non_positive = int((pd.to_numeric(frame["quantity"], errors="coerce") <= 0).sum()) if "quantity" in frame else 0
    trade_id_range_violations = int((frame["first_trade_id"] > frame["last_trade_id"]).sum()) if {"first_trade_id", "last_trade_id"}.issubset(frame) else 0
    if price_non_positive:
        errors.append("non-positive price rows detected")
    if quantity_non_positive:
        errors.append("non-positive quantity rows detected")
    if trade_id_range_violations:
        errors.append("first_trade_id > last_trade_id rows detected")

    critical_columns = [
        "aggregate_trade_id",
        "price",
        "quantity",
        "first_trade_id",
        "last_trade_id",
        "event_ts",
        "trade_ts",
        "available_ts",
        "decision_ts",
    ]
    null_critical_rows = int(frame[critical_columns].isna().any(axis=1).sum()) if set(critical_columns).issubset(frame) else len(frame)
    if null_critical_rows:
        errors.append("null critical rows detected")

    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    trade_ts = pd.to_datetime(frame["trade_ts"], utc=True)
    available_ts = pd.to_datetime(frame["available_ts"], utc=True)
    decision_ts = pd.to_datetime(frame["decision_ts"], utc=True)
    available_before_trade = int((available_ts < trade_ts).sum())
    decision_before_available = int((decision_ts < available_ts).sum())
    if available_before_trade:
        errors.append("available_ts before trade_ts rows detected")
    if decision_before_available:
        errors.append("decision_ts before available_ts rows detected")

    bool_errors = [
        column
        for column in ["is_buyer_maker", "is_best_match"]
        if column in frame and str(frame[column].dtype) != "bool"
    ]
    if bool_errors:
        errors.append(f"non-bool columns detected: {bool_errors}")

    return {
        "rows": int(len(frame)),
        "duplicate_aggregate_trade_ids": duplicate_ids,
        "missing_dates": [],
        "non_monotonic_trade_ids": non_monotonic_trade_ids,
        "non_monotonic_event_ts": non_monotonic_event_ts,
        "price_non_positive_rows": price_non_positive,
        "quantity_non_positive_rows": quantity_non_positive,
        "trade_id_range_violations": trade_id_range_violations,
        "null_critical_rows": null_critical_rows,
        "min_event_ts": event_ts.min().isoformat().replace("+00:00", "Z") if len(frame) else None,
        "max_event_ts": event_ts.max().isoformat().replace("+00:00", "Z") if len(frame) else None,
        "timestamps_utc": _timestamps_are_utc(frame, ["event_ts", "trade_ts", "available_ts", "decision_ts"]),
        "timestamp_order_valid": available_before_trade == 0 and decision_before_available == 0,
        "forbidden_columns_present": forbidden,
        "errors": errors,
        "warnings": warnings,
    }


def _non_monotonic_count(series: pd.Series) -> int:
    if len(series) <= 1:
        return 0
    return int((series.diff().dropna() < pd.Timedelta(0)).sum()) if pd.api.types.is_datetime64_any_dtype(series) else int((series.diff().dropna() < 0).sum())


def _timestamps_are_utc(frame: pd.DataFrame, columns: list[str]) -> bool:
    for column in columns:
        if column not in frame:
            return False
        if "UTC" not in str(frame[column].dtype):
            return False
    return True
