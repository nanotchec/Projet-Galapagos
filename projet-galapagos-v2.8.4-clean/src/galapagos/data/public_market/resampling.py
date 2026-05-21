from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from galapagos.data.public_market.schemas import OHLCV_COLUMNS


TARGET_TIMEFRAMES = {
    "5m": {"minutes": 5, "expected_rows": 288, "pandas_freq": "5min"},
    "15m": {"minutes": 15, "expected_rows": 96, "pandas_freq": "15min"},
    "1h": {"minutes": 60, "expected_rows": 24, "pandas_freq": "1h"},
}


@dataclass(frozen=True)
class ResamplingSpec:
    target_timeframe: str
    minutes: int
    expected_rows: int
    pandas_freq: str


def resample_ohlcv(
    frame_1m: pd.DataFrame,
    *,
    target_timeframe: str,
    source_timeframe: str = "1m",
) -> pd.DataFrame:
    if source_timeframe != "1m":
        raise ValueError("V2.4 resampling supports source_timeframe=1m only.")
    spec = get_resampling_spec(target_timeframe)
    _validate_input_frame(frame_1m)
    frame = frame_1m.copy()
    frame["event_ts"] = pd.to_datetime(frame["event_ts"], utc=True)
    frame["close_ts"] = pd.to_datetime(frame["close_ts"], utc=True)
    frame["available_ts"] = pd.to_datetime(frame["available_ts"], utc=True)
    frame["decision_ts"] = pd.to_datetime(frame["decision_ts"], utc=True)
    frame["ingested_at_ts"] = pd.to_datetime(frame["ingested_at_ts"], utc=True)
    if not frame["event_ts"].is_monotonic_increasing:
        raise ValueError("source 1m event_ts must be physically monotonic before resampling.")
    frame["_bucket"] = frame["event_ts"].dt.floor(spec.pandas_freq)
    bucket_sizes = frame.groupby("_bucket", sort=True).size()
    if not (bucket_sizes == spec.minutes).all():
        raise ValueError("source 1m rows contain a partial or incomplete resampling bucket.")
    rows = []
    metadata_columns = [
        "source",
        "venue",
        "market_type",
        "symbol",
        "raw_file_sha256",
        "ingestion_run_id",
        "ingested_at_ts",
        "source_timestamp_unit",
    ]
    for _bucket, group in frame.groupby("_bucket", sort=True):
        group = group.sort_values("event_ts").reset_index(drop=True)
        _validate_constant_metadata(group, metadata_columns)
        first = group.iloc[0]
        last = group.iloc[-1]
        rows.append(
            {
                "source": first["source"],
                "venue": first["venue"],
                "market_type": first["market_type"],
                "symbol": first["symbol"],
                "timeframe": target_timeframe,
                "event_ts": first["event_ts"],
                "close_ts": last["close_ts"],
                "available_ts": last["close_ts"],
                "decision_ts": last["close_ts"],
                "ingested_at_ts": first["ingested_at_ts"],
                "open": float(first["open"]),
                "high": float(group["high"].max()),
                "low": float(group["low"].min()),
                "close": float(last["close"]),
                "volume": float(group["volume"].sum()),
                "quote_volume": float(group["quote_volume"].sum()),
                "trade_count": int(group["trade_count"].sum()),
                "taker_buy_base_volume": float(group["taker_buy_base_volume"].sum()),
                "taker_buy_quote_volume": float(group["taker_buy_quote_volume"].sum()),
                "source_open_time_raw": int(first["source_open_time_raw"]),
                "source_close_time_raw": int(last["source_close_time_raw"]),
                "source_timestamp_unit": first["source_timestamp_unit"],
                "raw_file_sha256": first["raw_file_sha256"],
                "ingestion_run_id": first["ingestion_run_id"],
            }
        )
    result = pd.DataFrame(rows, columns=OHLCV_COLUMNS)
    if len(result) != spec.expected_rows:
        raise ValueError(f"resampled {target_timeframe} rows {len(result)} != expected {spec.expected_rows}")
    return result.sort_values("event_ts").reset_index(drop=True)


def get_resampling_spec(target_timeframe: str) -> ResamplingSpec:
    payload = TARGET_TIMEFRAMES.get(target_timeframe)
    if payload is None:
        raise ValueError("V2.4 supports target_timeframe=5m, 15m or 1h only.")
    return ResamplingSpec(
        target_timeframe=target_timeframe,
        minutes=int(payload["minutes"]),
        expected_rows=int(payload["expected_rows"]),
        pandas_freq=str(payload["pandas_freq"]),
    )


def _validate_input_frame(frame: pd.DataFrame) -> None:
    missing = [column for column in OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"source 1m missing columns: {missing}")
    if set(frame["timeframe"].astype(str).unique()) != {"1m"}:
        raise ValueError("source frame must contain timeframe=1m only.")
    if frame[["raw_file_sha256", "ingestion_run_id", "ingested_at_ts"]].isna().any().any():
        raise ValueError("source provenance columns must not contain null values.")


def _validate_constant_metadata(group: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if group[column].nunique(dropna=False) != 1:
            raise ValueError(f"metadata column {column} is not constant inside resampling bucket.")
