from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from galapagos.data.public_market.schemas import CRITICAL_COLUMNS, UNIQUE_KEY_COLUMNS

TIMEFRAME_DELTAS = {
    "1m": pd.Timedelta(minutes=1),
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "1h": pd.Timedelta(hours=1),
}


@dataclass(frozen=True)
class QualityResult:
    payload: dict[str, Any]
    passed: bool


def assess_ohlcv_quality(frame: pd.DataFrame, *, expected_rows: int, timeframe: str) -> QualityResult:
    errors: list[str] = []
    warnings: list[str] = []
    missing_columns = [column for column in CRITICAL_COLUMNS if column not in frame.columns]
    if missing_columns:
        errors.append(f"missing critical columns: {missing_columns}")
        return QualityResult(_empty_quality(expected_rows, errors), False)

    duplicate_rows = int(frame.duplicated(subset=UNIQUE_KEY_COLUMNS).sum())
    null_critical_rows = int(frame[CRITICAL_COLUMNS].isna().any(axis=1).sum())
    ohlc_mask = ~(
        (frame["high"] >= frame["low"])
        & (frame["high"] >= frame["open"])
        & (frame["high"] >= frame["close"])
        & (frame["low"] <= frame["open"])
        & (frame["low"] <= frame["close"])
        & (frame["open"] > 0)
        & (frame["high"] > 0)
        & (frame["low"] > 0)
        & (frame["close"] > 0)
    )
    ohlc_violations = int(ohlc_mask.sum())
    negative_volume_rows = int((frame["volume"] < 0).sum())

    temporal = _temporal_quality(frame, timeframe=timeframe)
    if len(frame) != expected_rows:
        errors.append(f"rows {len(frame)} != expected_rows {expected_rows}")
    if duplicate_rows:
        errors.append("duplicate OHLCV keys detected")
    if temporal["gap_count"]:
        errors.append("temporal gaps detected")
    if not temporal["monotonic_event_ts"]:
        errors.append("event_ts is not monotonic increasing")
    if not temporal["timestamp_order_valid"]:
        errors.append("timestamp order violation")
    if not temporal["timestamps_utc"]:
        errors.append("timestamps must be timezone-aware UTC")
    if ohlc_violations:
        errors.append("OHLC invariant violation")
    if negative_volume_rows:
        errors.append("negative volume rows detected")
    if null_critical_rows:
        errors.append("null critical rows detected")

    payload = {
        "rows": int(len(frame)),
        "expected_rows": int(expected_rows),
        "duplicate_rows": duplicate_rows,
        "gap_count": int(temporal["gap_count"]),
        "gaps": temporal["gaps"],
        "ohlc_violations": ohlc_violations,
        "negative_volume_rows": negative_volume_rows,
        "null_critical_rows": null_critical_rows,
        "min_event_ts": _iso_or_none(frame["event_ts"].min()) if len(frame) else None,
        "max_event_ts": _iso_or_none(frame["event_ts"].max()) if len(frame) else None,
        "min_close_ts": _iso_or_none(frame["close_ts"].min()) if len(frame) else None,
        "max_close_ts": _iso_or_none(frame["close_ts"].max()) if len(frame) else None,
        "monotonic_event_ts": bool(temporal["monotonic_event_ts"]),
        "timestamp_order_valid": bool(temporal["timestamp_order_valid"]),
        "timestamps_utc": bool(temporal["timestamps_utc"]),
        "errors": errors,
        "warnings": warnings,
    }
    return QualityResult(payload, not errors)


def _temporal_quality(frame: pd.DataFrame, *, timeframe: str) -> dict[str, Any]:
    if timeframe not in TIMEFRAME_DELTAS:
        raise ValueError("quality checks support timeframe=1m, 5m, 15m or 1h only.")
    if frame.empty:
        return {
            "gap_count": 0,
            "gaps": [],
            "monotonic_event_ts": True,
            "timestamp_order_valid": True,
            "timestamps_utc": True,
        }
    physical_event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    physical_monotonic = bool(physical_event_ts.is_monotonic_increasing)
    ordered = frame.sort_values("event_ts").reset_index(drop=True)
    event_ts = pd.to_datetime(ordered["event_ts"], utc=True)
    close_ts = pd.to_datetime(ordered["close_ts"], utc=True)
    available_ts = pd.to_datetime(ordered["available_ts"], utc=True)
    decision_ts = pd.to_datetime(ordered["decision_ts"], utc=True)
    gaps = []
    diffs = event_ts.diff().dropna()
    expected_delta = TIMEFRAME_DELTAS[timeframe]
    for index, delta in diffs.items():
        if delta != expected_delta:
            gaps.append(
                {
                    "previous_event_ts": _iso_or_none(event_ts.iloc[index - 1]),
                    "next_event_ts": _iso_or_none(event_ts.iloc[index]),
                    "delta_seconds": int(delta.total_seconds()),
                }
            )
    timestamp_order_valid = bool(
        ((event_ts < close_ts) & (close_ts <= available_ts) & (available_ts <= decision_ts)).all()
    )
    return {
        "gap_count": len(gaps),
        "gaps": gaps[:20],
        "monotonic_event_ts": physical_monotonic,
        "timestamp_order_valid": timestamp_order_valid,
        "timestamps_utc": all(_is_utc(series) for series in (event_ts, close_ts, available_ts, decision_ts)),
    }


def _is_utc(series: pd.Series) -> bool:
    return str(series.dt.tz) == "UTC"


def _iso_or_none(value: Any) -> str | None:
    if pd.isna(value):
        return None
    return pd.Timestamp(value).tz_convert("UTC").isoformat().replace("+00:00", "Z")


def _empty_quality(expected_rows: int, errors: list[str]) -> dict[str, Any]:
    return {
        "rows": 0,
        "expected_rows": expected_rows,
        "duplicate_rows": 0,
        "gap_count": 0,
        "gaps": [],
        "ohlc_violations": 0,
        "negative_volume_rows": 0,
        "null_critical_rows": 0,
        "min_event_ts": None,
        "max_event_ts": None,
        "min_close_ts": None,
        "max_close_ts": None,
        "monotonic_event_ts": False,
        "timestamp_order_valid": False,
        "timestamps_utc": False,
        "errors": errors,
        "warnings": [],
    }
