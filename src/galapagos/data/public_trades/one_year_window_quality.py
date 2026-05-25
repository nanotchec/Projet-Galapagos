from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_trades.quality import assess_agg_trades_frame
from galapagos.data.public_trades.schemas import AGG_TRADE_COLUMNS_V8_2, FORBIDDEN_TRADE_COLUMNS_V8_2


def assess_one_year_agg_trade_partitions_v8_2(
    root: Path,
    partitions: dict[str, dict[str, Any]],
    *,
    expected_days: int,
    missing_dates: list[str],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = 0
    duplicate_ids = 0
    non_monotonic_trade_ids = 0
    non_monotonic_event_ts = 0
    price_non_positive_rows = 0
    quantity_non_positive_rows = 0
    trade_id_range_violations = 0
    null_critical_rows = 0
    timestamps_utc = True
    timestamp_order_valid = True
    forbidden_columns: set[str] = set()
    min_event_ts: pd.Timestamp | None = None
    max_event_ts: pd.Timestamp | None = None
    previous_last_trade_id: int | None = None
    previous_max_event_ts: pd.Timestamp | None = None

    for date_key in sorted(partitions):
        payload = partitions[date_key]
        path = root / payload["path"]
        frame = pd.read_parquet(path, engine="pyarrow")
        local = assess_agg_trades_frame(frame, expected_rows=int(payload["rows"]))
        if list(frame.columns) != AGG_TRADE_COLUMNS_V8_2:
            errors.append(f"{date_key}: AGG_TRADE_COLUMNS_V8_2 schema mismatch")
        errors.extend(f"{date_key}: {error}" for error in local["errors"])
        rows += int(local["rows"])
        duplicate_ids += int(local["duplicate_aggregate_trade_ids"])
        non_monotonic_trade_ids += int(local["non_monotonic_trade_ids"])
        non_monotonic_event_ts += int(local["non_monotonic_event_ts"])
        price_non_positive_rows += int(local["price_non_positive_rows"])
        quantity_non_positive_rows += int(local["quantity_non_positive_rows"])
        trade_id_range_violations += int(local["trade_id_range_violations"])
        null_critical_rows += int(local["null_critical_rows"])
        timestamps_utc = timestamps_utc and bool(local["timestamps_utc"])
        timestamp_order_valid = timestamp_order_valid and bool(local["timestamp_order_valid"])
        forbidden_columns.update(local["forbidden_columns_present"])
        forbidden_columns.update(column for column in frame.columns if column.casefold() in FORBIDDEN_TRADE_COLUMNS_V8_2)

        event_ts = pd.to_datetime(frame["event_ts"], utc=True)
        local_min_event_ts = event_ts.min()
        local_max_event_ts = event_ts.max()
        local_first_trade_id = int(frame["aggregate_trade_id"].iloc[0])
        local_last_trade_id = int(frame["aggregate_trade_id"].iloc[-1])
        if previous_last_trade_id is not None:
            if local_first_trade_id <= previous_last_trade_id:
                duplicate_ids += int(local_first_trade_id == previous_last_trade_id)
                non_monotonic_trade_ids += int(local_first_trade_id < previous_last_trade_id)
                errors.append(f"{date_key}: aggregate_trade_id boundary is not strictly increasing")
            if local_min_event_ts < previous_max_event_ts:
                non_monotonic_event_ts += 1
                errors.append(f"{date_key}: event_ts boundary is not non-decreasing")
        previous_last_trade_id = local_last_trade_id
        previous_max_event_ts = local_max_event_ts
        min_event_ts = local_min_event_ts if min_event_ts is None else min(min_event_ts, local_min_event_ts)
        max_event_ts = local_max_event_ts if max_event_ts is None else max(max_event_ts, local_max_event_ts)

    if missing_dates:
        errors.append(f"missing aggTrades dates in V8.2 window: {missing_dates}")
    if len(partitions) != expected_days - len(missing_dates):
        errors.append("V8.2 partition count does not match expected available days")
    if forbidden_columns:
        errors.append(f"forbidden columns present: {sorted(forbidden_columns)}")

    return {
        "rows": int(rows),
        "expected_days": int(expected_days),
        "raw_files_count": int(len(partitions)),
        "duplicate_aggregate_trade_ids": int(duplicate_ids),
        "missing_dates": list(missing_dates),
        "non_monotonic_trade_ids": int(non_monotonic_trade_ids),
        "non_monotonic_event_ts": int(non_monotonic_event_ts),
        "price_non_positive_rows": int(price_non_positive_rows),
        "quantity_non_positive_rows": int(quantity_non_positive_rows),
        "trade_id_range_violations": int(trade_id_range_violations),
        "null_critical_rows": int(null_critical_rows),
        "min_event_ts": min_event_ts.isoformat().replace("+00:00", "Z") if min_event_ts is not None else None,
        "max_event_ts": max_event_ts.isoformat().replace("+00:00", "Z") if max_event_ts is not None else None,
        "timestamps_utc": bool(timestamps_utc),
        "timestamp_order_valid": bool(timestamp_order_valid),
        "forbidden_columns_present": sorted(forbidden_columns),
        "errors": errors,
        "warnings": warnings,
    }
