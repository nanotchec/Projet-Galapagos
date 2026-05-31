from __future__ import annotations

import gc
import json
import os
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45_schemas import (
    EXPECTED_DAYS,
    EXPECTED_ROWS_BY_TIMEFRAME,
    EXPECTED_TIMEFRAMES,
    FEATURE_COLUMNS,
    FEATURE_FAMILIES,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_FEATURE_COLUMNS,
    SOURCE,
    SOURCE_AGGTRADES_VALIDATION_VERSION,
    STRICT_COLUMNS,
    SYMBOL,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
)


VERSION = "V9.45"
SOURCE_VERSION = "V9.44"
LAST_VALIDATED_VERSION = "V9.44"
DIRECTION = "aggtrades_exact_5y_feature_enrichment"

REPORT_JSON_PATH = Path("reports/features/aggtrades_exact_5y_feature_enrichment_v9_45.json")
REPORT_MD_PATH = Path("reports/features/aggtrades_exact_5y_feature_enrichment_v9_45.md")
MANIFEST_PATH = Path("reports/manifests/aggtrades_exact_5y_feature_enrichment_v9_45_manifest.json")
DOC_PATH = Path("docs/aggtrades_exact_5y_feature_enrichment_v9_45.md")

INPUT_PATHS = {
    "v9_44_diagnostic": Path("reports/research_decisions/ohlcv_aggtrades_5y_ml_diagnostic_v9_44.json"),
    "v9_44_manifest": Path("reports/manifests/ohlcv_aggtrades_5y_ml_diagnostic_v9_44_manifest.json"),
    "v9_43_ml": Path("reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json"),
    "v9_42_dataset_validation": Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json"),
    "v9_38_feature_validation": Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
    "v9_37_feature_store": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
    "v9_32_aggtrades_validation": Path("reports/data/aggtrades_5y_full_coverage_validation_v9_32.json"),
    "v9_36_ohlcv_validation": Path("reports/data/ohlcv_from_aggtrades_5y_validation_v9_36.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

SAFETY_FLAGS = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_walk_forward": True,
    "no_ml": True,
    "no_dataset_supervised": True,
    "no_labels": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "exchange_auth_used": False,
    "websocket_live_used": False,
    "network_used": False,
    "no_new_data_download": True,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

FINDINGS = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}


def run_aggtrades_exact_5y_feature_enrichment_v9_45(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    started = time.monotonic()
    run_id = f"v9_45_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    preflight = build_preflight_v9_45(root)
    inputs = {name: _read_optional_json(root / path) for name, path in INPUT_PATHS.items()}
    output_paths = {timeframe: exact_feature_output_path_v9_45(root, timeframe) for timeframe in EXPECTED_TIMEFRAMES}
    timeframe_reports: dict[str, dict[str, Any]] = {}
    created = False
    if preflight["safe_to_run_exact_enrichment"] and _sources_ready(inputs):
        if existing_exact_feature_files_ready_v9_45(output_paths):
            print("[V9.45] existing feature files detected; refreshing reports only", flush=True)
            for timeframe, output_path in output_paths.items():
                frame = pd.read_parquet(output_path, engine="pyarrow")
                timeframe_report = validate_exact_feature_frame_v9_45(frame, timeframe=timeframe, output_path=output_path)
                timeframe_reports[timeframe] = timeframe_report
                _write_json(root / timeframe_report_path_v9_45(timeframe), timeframe_report)
                del frame
                gc.collect()
        else:
            frames_by_timeframe = build_exact_features_by_timeframe_v9_45(root, run_id=run_id)
            for timeframe, frame in frames_by_timeframe.items():
                output_path = output_paths[timeframe]
                output_path.parent.mkdir(parents=True, exist_ok=True)
                frame.to_parquet(output_path, index=False, engine="pyarrow", compression="zstd")
                timeframe_report = validate_exact_feature_frame_v9_45(frame, timeframe=timeframe, output_path=output_path)
                timeframe_reports[timeframe] = timeframe_report
                _write_json(root / timeframe_report_path_v9_45(timeframe), timeframe_report)
                del frame
                gc.collect()
        if not timeframe_reports:
            raise RuntimeError("V9.45 exact feature enrichment produced no timeframe reports")
        created = True
    else:
        for timeframe in EXPECTED_TIMEFRAMES:
            timeframe_reports[timeframe] = _blocked_timeframe_report(timeframe, preflight)
            _write_json(root / timeframe_report_path_v9_45(timeframe), timeframe_reports[timeframe])
    report = build_global_report_v9_45(
        root=root,
        run_id=run_id,
        preflight=preflight,
        inputs=inputs,
        timeframe_reports=timeframe_reports,
        output_paths=output_paths,
        runtime_seconds=round(time.monotonic() - started, 3),
        created=created,
    )
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_45(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_45(report))
    update_state_surfaces_v9_45(root, report)
    return report


def existing_exact_feature_files_ready_v9_45(output_paths: dict[str, Path]) -> bool:
    return all(output_paths[timeframe].is_file() and output_paths[timeframe].stat().st_size > 0 for timeframe in EXPECTED_TIMEFRAMES)


def create_exact_feature_files_duckdb_v9_45(root: Path, *, run_id: str, output_paths: dict[str, Path]) -> None:
    import duckdb

    con = duckdb.connect(database=":memory:")
    con.execute("PRAGMA threads=4")
    con.execute("PRAGMA memory_limit='12GB'")
    source_glob = (root / "data/silver/public_trades/venue=binance/market_type=spot/symbol=BTCUSDT/date=*/agg_trades.parquet").as_posix()
    for timeframe in EXPECTED_TIMEFRAMES:
        output_path = output_paths[timeframe]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink()
        print(f"[V9.45] duckdb_timeframe_start={timeframe}", flush=True)
        con.execute(_duckdb_feature_sql_v9_45(source_glob, output_path.as_posix(), timeframe, run_id))
        print(f"[V9.45] duckdb_timeframe_done={timeframe} output={output_path.as_posix()}", flush=True)
    con.close()


def _duckdb_feature_sql_v9_45(source_glob: str, output_path: str, timeframe: str, run_id: str) -> str:
    interval = {"1m": "1 minute", "5m": "5 minutes", "15m": "15 minutes", "1h": "1 hour"}[timeframe]
    seconds = _timeframe_seconds(timeframe)
    source = source_glob.replace("'", "''")
    output = output_path.replace("'", "''")
    escaped_run_id = run_id.replace("'", "''")
    return f"""
COPY (
WITH source AS (
    SELECT
        CAST(event_ts AS TIMESTAMP) AS event_ts,
        CAST(available_ts AS TIMESTAMP) AS available_ts,
        CAST(quantity AS DOUBLE) AS quantity,
        CAST(price AS DOUBLE) AS price,
        CAST(quantity AS DOUBLE) * CAST(price AS DOUBLE) AS quote_quantity,
        CAST(is_buyer_maker AS BOOLEAN) AS is_buyer_maker,
        NOT CAST(is_buyer_maker AS BOOLEAN) AS is_taker_buy,
        time_bucket(INTERVAL '{interval}', CAST(event_ts AS TIMESTAMP)) AS bucket_start,
        date_trunc('second', CAST(event_ts AS TIMESTAMP)) AS event_second
    FROM read_parquet('{source}', hive_partitioning=true)
    WHERE CAST(event_ts AS TIMESTAMP) >= TIMESTAMP '{TARGET_WINDOW_START} 00:00:00'
      AND CAST(event_ts AS TIMESTAMP) < TIMESTAMP '2026-05-06 00:00:00'
),
grid AS (
    SELECT open_ts AS bucket_start
    FROM generate_series(
        TIMESTAMP '{TARGET_WINDOW_START} 00:00:00',
        TIMESTAMP '2026-05-06 00:00:00' - INTERVAL '{interval}',
        INTERVAL '{interval}'
    ) AS t(open_ts)
),
agg AS (
    SELECT
        bucket_start,
        count(*)::BIGINT AS agg_trade_count_exact,
        sum(CASE WHEN is_taker_buy THEN 1 ELSE 0 END)::BIGINT AS taker_buy_count_exact,
        sum(CASE WHEN is_buyer_maker THEN 1 ELSE 0 END)::BIGINT AS buyer_maker_true_count_exact,
        sum(quantity)::DOUBLE AS agg_trade_volume_exact,
        sum(quote_quantity)::DOUBLE AS agg_trade_quote_volume_exact,
        sum(CASE WHEN is_taker_buy THEN quantity ELSE 0 END)::DOUBLE AS taker_buy_base_volume_exact,
        sum(CASE WHEN is_taker_buy THEN quote_quantity ELSE 0 END)::DOUBLE AS taker_buy_quote_volume_exact,
        min(event_ts) AS first_trade_ts,
        max(event_ts) AS last_trade_ts,
        median(quantity)::DOUBLE AS median_trade_size_exact,
        quantile_cont(quantity, 0.75)::DOUBLE AS p75_trade_size_exact,
        quantile_cont(quantity, 0.90)::DOUBLE AS p90_trade_size_exact,
        quantile_cont(quantity, 0.95)::DOUBLE AS p95_trade_size_exact,
        quantile_cont(quantity, 0.99)::DOUBLE AS p99_trade_size_exact,
        max(quantity)::DOUBLE AS max_trade_size_exact
    FROM source
    GROUP BY bucket_start
),
large AS (
    SELECT
        s.bucket_start,
        sum(CASE WHEN s.quantity >= a.p95_trade_size_exact THEN 1 ELSE 0 END)::BIGINT AS large_trade_count_p95_exact,
        sum(CASE WHEN s.quantity >= a.p95_trade_size_exact THEN s.quantity ELSE 0 END)::DOUBLE AS large_trade_volume_p95_exact,
        sum(CASE WHEN s.quantity >= a.p99_trade_size_exact THEN 1 ELSE 0 END)::BIGINT AS large_trade_count_p99_exact,
        sum(CASE WHEN s.quantity >= a.p99_trade_size_exact THEN s.quantity ELSE 0 END)::DOUBLE AS large_trade_volume_p99_exact
    FROM source s
    JOIN agg a ON s.bucket_start = a.bucket_start
    GROUP BY s.bucket_start
),
size_buckets AS (
    SELECT
        bucket_start,
        sum(CASE WHEN quantity < 0.01 THEN 1 ELSE 0 END)::BIGINT AS trade_size_bucket_small_count,
        sum(CASE WHEN quantity >= 0.01 AND quantity < 0.1 THEN 1 ELSE 0 END)::BIGINT AS trade_size_bucket_medium_count,
        sum(CASE WHEN quantity >= 0.1 AND quantity < 1.0 THEN 1 ELSE 0 END)::BIGINT AS trade_size_bucket_large_count,
        sum(CASE WHEN quantity >= 1.0 THEN 1 ELSE 0 END)::BIGINT AS trade_size_bucket_whale_count
    FROM source
    GROUP BY bucket_start
),
per_second AS (
    SELECT
        bucket_start,
        event_second,
        count(*)::BIGINT AS second_count,
        sum(quantity)::DOUBLE AS second_volume
    FROM source
    GROUP BY bucket_start, event_second
),
burst AS (
    SELECT
        bucket_start,
        count(*)::BIGINT AS active_seconds_count,
        avg(second_count)::DOUBLE AS agg_trade_count_per_second_mean,
        max(second_count)::DOUBLE AS agg_trade_count_per_second_max,
        max(second_count)::DOUBLE AS max_trades_in_1s,
        max(second_volume)::DOUBLE AS max_volume_in_1s,
        quantile_cont(second_count, 0.95)::DOUBLE AS burst_count_1s_p95,
        quantile_cont(second_volume, 0.95)::DOUBLE AS burst_volume_1s_p95
    FROM per_second
    GROUP BY bucket_start
),
base AS (
    SELECT
        '{SOURCE}' AS source,
        'binance' AS venue,
        'spot' AS market_type,
        '{SYMBOL}' AS symbol,
        '{timeframe}' AS timeframe,
        g.bucket_start AS event_ts,
        g.bucket_start AS open_ts,
        g.bucket_start + INTERVAL '{interval}' AS close_ts,
        g.bucket_start + INTERVAL '{interval}' AS decision_ts,
        g.bucket_start + INTERVAL '{interval}' AS available_ts,
        g.bucket_start + INTERVAL '{interval}' AS feature_available_ts,
        '{escaped_run_id}' AS feature_run_id,
        '{FEATURE_SCHEMA_VERSION}' AS feature_schema_version,
        '{SOURCE_AGGTRADES_VALIDATION_VERSION}' AS source_aggtrades_validation_version,
        '{TARGET_WINDOW_START}' AS source_window_start,
        '{TARGET_WINDOW_END}' AS source_window_end,
        'bucket_complete_descriptive_no_future_beyond_decision_ts' AS quantile_threshold_method,
        COALESCE(a.agg_trade_count_exact, 0)::BIGINT AS agg_trade_count_exact,
        COALESCE(a.taker_buy_count_exact, 0)::BIGINT AS taker_buy_count_exact,
        COALESCE(a.buyer_maker_true_count_exact, 0)::BIGINT AS taker_sell_count_exact,
        COALESCE(a.buyer_maker_true_count_exact, 0)::BIGINT AS buyer_maker_true_count_exact,
        COALESCE(a.taker_buy_count_exact, 0)::BIGINT AS buyer_maker_false_count_exact,
        COALESCE(a.agg_trade_volume_exact, 0)::DOUBLE AS agg_trade_volume_exact,
        COALESCE(a.agg_trade_quote_volume_exact, 0)::DOUBLE AS agg_trade_quote_volume_exact,
        COALESCE(a.taker_buy_base_volume_exact, 0)::DOUBLE AS taker_buy_base_volume_exact,
        GREATEST(COALESCE(a.agg_trade_volume_exact, 0) - COALESCE(a.taker_buy_base_volume_exact, 0), 0)::DOUBLE AS taker_sell_base_volume_exact,
        COALESCE(a.taker_buy_quote_volume_exact, 0)::DOUBLE AS taker_buy_quote_volume_exact,
        GREATEST(COALESCE(a.agg_trade_quote_volume_exact, 0) - COALESCE(a.taker_buy_quote_volume_exact, 0), 0)::DOUBLE AS taker_sell_quote_volume_exact,
        CASE WHEN COALESCE(a.agg_trade_count_exact, 0) = 0 THEN 0 ELSE (COALESCE(a.taker_buy_count_exact, 0) - COALESCE(a.buyer_maker_true_count_exact, 0))::DOUBLE / COALESCE(a.agg_trade_count_exact, 1) END AS taker_buy_sell_count_imbalance_exact,
        CASE WHEN COALESCE(a.agg_trade_volume_exact, 0) = 0 THEN 0 ELSE (COALESCE(a.taker_buy_base_volume_exact, 0) - GREATEST(COALESCE(a.agg_trade_volume_exact, 0) - COALESCE(a.taker_buy_base_volume_exact, 0), 0)) / COALESCE(a.agg_trade_volume_exact, 1) END AS taker_buy_sell_volume_imbalance_exact,
        CASE WHEN COALESCE(a.agg_trade_volume_exact, 0) = 0 THEN 0 ELSE COALESCE(a.taker_buy_base_volume_exact, 0) / COALESCE(a.agg_trade_volume_exact, 1) END AS taker_buy_ratio_exact,
        CASE WHEN COALESCE(a.agg_trade_volume_exact, 0) = 0 THEN 0 ELSE GREATEST(COALESCE(a.agg_trade_volume_exact, 0) - COALESCE(a.taker_buy_base_volume_exact, 0), 0) / COALESCE(a.agg_trade_volume_exact, 1) END AS taker_sell_ratio_exact,
        CASE WHEN COALESCE(a.agg_trade_count_exact, 0) = 0 THEN 0 ELSE COALESCE(a.agg_trade_volume_exact, 0) / COALESCE(a.agg_trade_count_exact, 1) END AS average_trade_size_exact,
        COALESCE(a.median_trade_size_exact, 0)::DOUBLE AS median_trade_size_exact,
        COALESCE(a.p75_trade_size_exact, 0)::DOUBLE AS p75_trade_size_exact,
        COALESCE(a.p90_trade_size_exact, 0)::DOUBLE AS p90_trade_size_exact,
        COALESCE(a.p95_trade_size_exact, 0)::DOUBLE AS p95_trade_size_exact,
        COALESCE(a.p99_trade_size_exact, 0)::DOUBLE AS p99_trade_size_exact,
        COALESCE(a.max_trade_size_exact, 0)::DOUBLE AS max_trade_size_exact,
        COALESCE(l.large_trade_count_p95_exact, 0)::BIGINT AS large_trade_count_p95_exact,
        COALESCE(l.large_trade_volume_p95_exact, 0)::DOUBLE AS large_trade_volume_p95_exact,
        COALESCE(l.large_trade_count_p99_exact, 0)::BIGINT AS large_trade_count_p99_exact,
        COALESCE(l.large_trade_volume_p99_exact, 0)::DOUBLE AS large_trade_volume_p99_exact,
        COALESCE(sb.trade_size_bucket_small_count, 0)::BIGINT AS trade_size_bucket_small_count,
        COALESCE(sb.trade_size_bucket_medium_count, 0)::BIGINT AS trade_size_bucket_medium_count,
        COALESCE(sb.trade_size_bucket_large_count, 0)::BIGINT AS trade_size_bucket_large_count,
        COALESCE(sb.trade_size_bucket_whale_count, 0)::BIGINT AS trade_size_bucket_whale_count,
        COALESCE(b.agg_trade_count_per_second_mean, 0)::DOUBLE AS agg_trade_count_per_second_mean,
        COALESCE(b.agg_trade_count_per_second_max, 0)::DOUBLE AS agg_trade_count_per_second_max,
        COALESCE(b.max_trades_in_1s, 0)::DOUBLE AS max_trades_in_1s,
        COALESCE(b.max_volume_in_1s, 0)::DOUBLE AS max_volume_in_1s,
        COALESCE(b.burst_count_1s_p95, 0)::DOUBLE AS burst_count_1s_p95,
        COALESCE(b.burst_volume_1s_p95, 0)::DOUBLE AS burst_volume_1s_p95,
        COALESCE(a.first_trade_ts, g.bucket_start) AS first_trade_ts,
        COALESCE(a.last_trade_ts, g.bucket_start) AS last_trade_ts,
        COALESCE(b.active_seconds_count, 0)::BIGINT AS active_seconds_count,
        LEAST(COALESCE(b.active_seconds_count, 0)::DOUBLE / {seconds}, 1.0)::DOUBLE AS active_seconds_ratio,
        CASE WHEN a.first_trade_ts IS NULL THEN 0 ELSE date_diff('second', g.bucket_start, a.first_trade_ts) END::DOUBLE AS seconds_since_previous_trade_bucket_start,
        CASE WHEN a.last_trade_ts IS NULL THEN {seconds} ELSE date_diff('second', a.last_trade_ts, g.bucket_start + INTERVAL '{interval}') END::DOUBLE AS seconds_to_last_trade_bucket_end,
        CASE WHEN COALESCE(a.agg_trade_count_exact, 0) = 0 THEN 1 ELSE 0 END::TINYINT AS no_trade_bucket,
        0::TINYINT AS aggtrades_missing_flag,
        0::TINYINT AS aggtrades_partial_bucket_flag,
        0::BIGINT AS exact_feature_error_count,
        0::BIGINT AS exact_feature_null_count
    FROM grid g
    LEFT JOIN agg a ON g.bucket_start = a.bucket_start
    LEFT JOIN large l ON g.bucket_start = l.bucket_start
    LEFT JOIN size_buckets sb ON g.bucket_start = sb.bucket_start
    LEFT JOIN burst b ON g.bucket_start = b.bucket_start
),
final AS (
    SELECT
        *,
        avg(agg_trade_count_exact) OVER (ORDER BY open_ts ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)::DOUBLE AS rolling_exact_trade_count_mean_5,
        avg(agg_trade_count_exact) OVER (ORDER BY open_ts ROWS BETWEEN 14 PRECEDING AND CURRENT ROW)::DOUBLE AS rolling_exact_trade_count_mean_15,
        avg(agg_trade_count_exact) OVER (ORDER BY open_ts ROWS BETWEEN 59 PRECEDING AND CURRENT ROW)::DOUBLE AS rolling_exact_trade_count_mean_60,
        avg(taker_buy_sell_volume_imbalance_exact) OVER (ORDER BY open_ts ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)::DOUBLE AS rolling_exact_taker_imbalance_mean_5,
        avg(taker_buy_sell_volume_imbalance_exact) OVER (ORDER BY open_ts ROWS BETWEEN 14 PRECEDING AND CURRENT ROW)::DOUBLE AS rolling_exact_taker_imbalance_mean_15,
        avg(taker_buy_sell_volume_imbalance_exact) OVER (ORDER BY open_ts ROWS BETWEEN 59 PRECEDING AND CURRENT ROW)::DOUBLE AS rolling_exact_taker_imbalance_mean_60,
        avg(large_trade_count_p95_exact) OVER (ORDER BY open_ts ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)::DOUBLE AS rolling_large_trade_count_mean_5,
        avg(large_trade_count_p95_exact) OVER (ORDER BY open_ts ROWS BETWEEN 14 PRECEDING AND CURRENT ROW)::DOUBLE AS rolling_large_trade_count_mean_15,
        avg(large_trade_count_p95_exact) OVER (ORDER BY open_ts ROWS BETWEEN 59 PRECEDING AND CURRENT ROW)::DOUBLE AS rolling_large_trade_count_mean_60,
        TRUE AS row_valid_for_exact_features,
        '' AS feature_invalid_reason
    FROM base
)
SELECT {", ".join(STRICT_COLUMNS)}
FROM final
ORDER BY open_ts
) TO '{output}' (FORMAT PARQUET, COMPRESSION ZSTD)
"""


def build_exact_features_by_timeframe_v9_45(root: Path, *, run_id: str) -> dict[str, pd.DataFrame]:
    daily_frames: dict[str, list[pd.DataFrame]] = {timeframe: [] for timeframe in EXPECTED_TIMEFRAMES}
    days = _date_range(date.fromisoformat(TARGET_WINDOW_START), date.fromisoformat(TARGET_WINDOW_END))
    max_workers = int(os.environ.get("GALAPAGOS_V9_45_WORKERS", "12"))
    print(f"[V9.45] parallel_workers={max_workers} days={len(days)}", flush=True)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_build_day_features_worker_v9_45, root.as_posix(), day.isoformat(), run_id) for day in days]
        for index, future in enumerate(as_completed(futures), start=1):
            day_text, frames = future.result()
            for timeframe in EXPECTED_TIMEFRAMES:
                daily_frames[timeframe].append(frames[timeframe])
            if index == 1 or index % 25 == 0 or index == len(days):
                print(f"[V9.45] processed_days={index}/{len(days)} completed_day={day_text}", flush=True)
    outputs: dict[str, pd.DataFrame] = {}
    for timeframe, frames in daily_frames.items():
        frame = pd.concat(frames, ignore_index=True)
        frame = add_rolling_features_v9_45(frame)
        frame = finalize_feature_frame_v9_45(frame)
        outputs[timeframe] = frame
        del frames
        gc.collect()
    return outputs


def _build_day_features_worker_v9_45(root_text: str, day_text: str, run_id: str) -> tuple[str, dict[str, pd.DataFrame]]:
    root = Path(root_text)
    day = date.fromisoformat(day_text)
    source_path = silver_aggtrades_path_v9_45(root, day)
    day_frame = read_aggtrades_day_v9_45(source_path)
    frames = {
        timeframe: build_day_timeframe_features_v9_45(day_frame, day=day, timeframe=timeframe, run_id=run_id)
        for timeframe in EXPECTED_TIMEFRAMES
    }
    return day_text, frames


def read_aggtrades_day_v9_45(path: Path) -> pd.DataFrame:
    columns = ["aggregate_trade_id", "price", "quantity", "event_ts", "trade_ts", "is_buyer_maker", "available_ts"]
    frame = pd.read_parquet(path, columns=columns, engine="pyarrow")
    frame["event_ts"] = pd.to_datetime(frame["event_ts"], utc=True)
    frame["trade_ts"] = pd.to_datetime(frame["trade_ts"], utc=True)
    frame["available_ts"] = pd.to_datetime(frame["available_ts"], utc=True)
    frame["price"] = frame["price"].astype("float64")
    frame["quantity"] = frame["quantity"].astype("float64")
    frame["quote_quantity"] = frame["price"] * frame["quantity"]
    frame["is_taker_buy"] = ~frame["is_buyer_maker"].astype(bool)
    frame["event_second"] = frame["event_ts"].dt.floor("s")
    return frame


def build_day_timeframe_features_v9_45(day_frame: pd.DataFrame, *, day: date, timeframe: str, run_id: str) -> pd.DataFrame:
    freq = _pandas_freq(timeframe)
    bucket_index = pd.date_range(
        start=pd.Timestamp(day.isoformat(), tz="UTC"),
        end=pd.Timestamp((day + timedelta(days=1)).isoformat(), tz="UTC"),
        freq=freq,
        inclusive="left",
    )
    if day_frame.empty:
        grouped = pd.DataFrame(index=bucket_index)
    else:
        frame = day_frame.copy()
        frame["bucket_start"] = frame["event_ts"].dt.floor(freq)
        grouped = pd.DataFrame(index=bucket_index)
        groups = frame.groupby("bucket_start", sort=True, observed=True)
        grouped["agg_trade_count_exact"] = groups["aggregate_trade_id"].count()
        grouped["taker_buy_count_exact"] = groups["is_taker_buy"].sum()
        grouped["buyer_maker_true_count_exact"] = groups["is_buyer_maker"].sum()
        grouped["agg_trade_volume_exact"] = groups["quantity"].sum()
        grouped["agg_trade_quote_volume_exact"] = groups["quote_quantity"].sum()
        grouped["taker_buy_base_volume_exact"] = frame.loc[frame["is_taker_buy"]].groupby("bucket_start", observed=True)["quantity"].sum()
        grouped["taker_buy_quote_volume_exact"] = frame.loc[frame["is_taker_buy"]].groupby("bucket_start", observed=True)["quote_quantity"].sum()
        grouped["first_trade_ts"] = groups["event_ts"].min()
        grouped["last_trade_ts"] = groups["event_ts"].max()
        grouped["median_trade_size_exact"] = groups["quantity"].median()
        grouped["p75_trade_size_exact"] = groups["quantity"].quantile(0.75)
        grouped["p90_trade_size_exact"] = groups["quantity"].quantile(0.90)
        grouped["p95_trade_size_exact"] = groups["quantity"].quantile(0.95)
        grouped["p99_trade_size_exact"] = groups["quantity"].quantile(0.99)
        grouped["max_trade_size_exact"] = groups["quantity"].max()
        bucket_second = frame.groupby(["bucket_start", "event_second"], observed=True).agg(second_count=("aggregate_trade_id", "count"), second_volume=("quantity", "sum")).reset_index()
        second_groups = bucket_second.groupby("bucket_start", observed=True)
        grouped["active_seconds_count"] = second_groups["event_second"].count()
        grouped["agg_trade_count_per_second_mean"] = second_groups["second_count"].mean()
        grouped["agg_trade_count_per_second_max"] = second_groups["second_count"].max()
        grouped["max_trades_in_1s"] = second_groups["second_count"].max()
        grouped["max_volume_in_1s"] = second_groups["second_volume"].max()
        grouped["burst_count_1s_p95"] = second_groups["second_count"].quantile(0.95)
        grouped["burst_volume_1s_p95"] = second_groups["second_volume"].quantile(0.95)
        large = _large_trade_features(frame)
        grouped = grouped.join(large, how="left")
        buckets = _trade_size_bucket_counts(frame)
        grouped = grouped.join(buckets, how="left")
    output = grouped.reindex(bucket_index)
    output.index.name = "open_ts"
    output = output.reset_index()
    return decorate_feature_frame_v9_45(output, day=day, timeframe=timeframe, run_id=run_id)


def decorate_feature_frame_v9_45(frame: pd.DataFrame, *, day: date, timeframe: str, run_id: str) -> pd.DataFrame:
    seconds = _timeframe_seconds(timeframe)
    open_ts = pd.to_datetime(frame["open_ts"], utc=True)
    close_ts = open_ts + pd.to_timedelta(seconds, unit="s")
    count = frame["agg_trade_count_exact"].fillna(0).astype("int64")
    taker_buy_count = frame["taker_buy_count_exact"].fillna(0).astype("int64")
    buyer_maker_true_count = frame["buyer_maker_true_count_exact"].fillna(0).astype("int64")
    volume = frame["agg_trade_volume_exact"].fillna(0.0).astype("float64")
    quote_volume = frame["agg_trade_quote_volume_exact"].fillna(0.0).astype("float64")
    taker_buy_base = frame["taker_buy_base_volume_exact"].fillna(0.0).astype("float64")
    taker_buy_quote = frame["taker_buy_quote_volume_exact"].fillna(0.0).astype("float64")
    taker_sell_count = buyer_maker_true_count
    taker_sell_base = (volume - taker_buy_base).clip(lower=0.0)
    taker_sell_quote = (quote_volume - taker_buy_quote).clip(lower=0.0)
    output = pd.DataFrame(
        {
            "source": SOURCE,
            "venue": "binance",
            "market_type": "spot",
            "symbol": SYMBOL,
            "timeframe": timeframe,
            "event_ts": open_ts,
            "open_ts": open_ts,
            "close_ts": close_ts,
            "decision_ts": close_ts,
            "available_ts": close_ts,
            "feature_available_ts": close_ts,
            "feature_run_id": run_id,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "source_aggtrades_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
            "source_window_start": TARGET_WINDOW_START,
            "source_window_end": TARGET_WINDOW_END,
            "quantile_threshold_method": "bucket_complete_descriptive_no_future_beyond_decision_ts",
            "agg_trade_count_exact": count,
            "taker_buy_count_exact": taker_buy_count,
            "taker_sell_count_exact": taker_sell_count,
            "buyer_maker_true_count_exact": buyer_maker_true_count,
            "buyer_maker_false_count_exact": taker_buy_count,
            "agg_trade_volume_exact": volume,
            "agg_trade_quote_volume_exact": quote_volume,
            "taker_buy_base_volume_exact": taker_buy_base,
            "taker_sell_base_volume_exact": taker_sell_base,
            "taker_buy_quote_volume_exact": taker_buy_quote,
            "taker_sell_quote_volume_exact": taker_sell_quote,
        }
    )
    output["taker_buy_sell_count_imbalance_exact"] = _safe_ratio(taker_buy_count - taker_sell_count, taker_buy_count + taker_sell_count)
    output["taker_buy_sell_volume_imbalance_exact"] = _safe_ratio(taker_buy_base - taker_sell_base, taker_buy_base + taker_sell_base)
    output["taker_buy_ratio_exact"] = _safe_ratio(taker_buy_base, volume)
    output["taker_sell_ratio_exact"] = _safe_ratio(taker_sell_base, volume)
    output["average_trade_size_exact"] = _safe_ratio(volume, count)
    for col in ["median_trade_size_exact", "p75_trade_size_exact", "p90_trade_size_exact", "p95_trade_size_exact", "p99_trade_size_exact", "max_trade_size_exact", "large_trade_volume_p95_exact", "large_trade_volume_p99_exact", "agg_trade_count_per_second_mean", "agg_trade_count_per_second_max", "max_trades_in_1s", "max_volume_in_1s", "burst_count_1s_p95", "burst_volume_1s_p95"]:
        output[col] = frame.get(col, 0.0).fillna(0.0).astype("float64")
    for col in ["large_trade_count_p95_exact", "large_trade_count_p99_exact", "trade_size_bucket_small_count", "trade_size_bucket_medium_count", "trade_size_bucket_large_count", "trade_size_bucket_whale_count"]:
        output[col] = frame.get(col, 0).fillna(0).astype("int64")
    first_trade = pd.to_datetime(frame.get("first_trade_ts", open_ts), utc=True).fillna(open_ts)
    last_trade = pd.to_datetime(frame.get("last_trade_ts", open_ts), utc=True).fillna(open_ts)
    active_seconds = frame.get("active_seconds_count", 0).fillna(0).astype("int64")
    output["first_trade_ts"] = first_trade
    output["last_trade_ts"] = last_trade
    output["active_seconds_count"] = active_seconds
    output["active_seconds_ratio"] = (active_seconds / seconds).clip(lower=0.0, upper=1.0)
    output["seconds_since_previous_trade_bucket_start"] = ((first_trade - open_ts).dt.total_seconds()).clip(lower=0.0, upper=seconds).fillna(0.0)
    output["seconds_to_last_trade_bucket_end"] = ((close_ts - last_trade).dt.total_seconds()).clip(lower=0.0, upper=seconds).fillna(seconds)
    output["no_trade_bucket"] = (count == 0).astype("int8")
    output["aggtrades_missing_flag"] = 0
    output["aggtrades_partial_bucket_flag"] = 0
    output["exact_feature_error_count"] = 0
    output["exact_feature_null_count"] = 0
    for col in ["rolling_exact_trade_count_mean_5", "rolling_exact_trade_count_mean_15", "rolling_exact_trade_count_mean_60", "rolling_exact_taker_imbalance_mean_5", "rolling_exact_taker_imbalance_mean_15", "rolling_exact_taker_imbalance_mean_60", "rolling_large_trade_count_mean_5", "rolling_large_trade_count_mean_15", "rolling_large_trade_count_mean_60"]:
        output[col] = 0.0
    output["row_valid_for_exact_features"] = True
    output["feature_invalid_reason"] = ""
    return output[STRICT_COLUMNS]


def add_rolling_features_v9_45(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values("open_ts", kind="mergesort").reset_index(drop=True)
    for window in (5, 15, 60):
        ordered[f"rolling_exact_trade_count_mean_{window}"] = ordered["agg_trade_count_exact"].rolling(window=window, min_periods=1).mean()
        ordered[f"rolling_exact_taker_imbalance_mean_{window}"] = ordered["taker_buy_sell_volume_imbalance_exact"].rolling(window=window, min_periods=1).mean()
        ordered[f"rolling_large_trade_count_mean_{window}"] = ordered["large_trade_count_p95_exact"].rolling(window=window, min_periods=1).mean()
    return ordered


def finalize_feature_frame_v9_45(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["exact_feature_null_count"] = output[list(FEATURE_COLUMNS)].isna().sum(axis=1).astype("int64")
    output["feature_invalid_reason"] = np.where(output["exact_feature_null_count"] > 0, "feature_null_detected", "")
    output["row_valid_for_exact_features"] = output["exact_feature_null_count"] == 0
    return output[STRICT_COLUMNS]


def validate_exact_feature_frame_v9_45(frame: pd.DataFrame, *, timeframe: str, output_path: Path) -> dict[str, Any]:
    expected_rows = EXPECTED_ROWS_BY_TIMEFRAME[timeframe]
    duplicate_close_ts = int(frame["close_ts"].duplicated().sum())
    feature_null_count = int(frame[list(FEATURE_COLUMNS)].isna().sum().sum())
    invalid_rows = int((~frame["row_valid_for_exact_features"]).sum())
    leakage_violations = int((pd.to_datetime(frame["feature_available_ts"], utc=True) > pd.to_datetime(frame["decision_ts"], utc=True)).sum())
    forbidden = sorted([column for column in frame.columns if any(token in column.casefold() for token in FORBIDDEN_FEATURE_COLUMNS)])
    count_columns = [column for column in FEATURE_COLUMNS if ("count" in column or column.endswith("_flag")) and "imbalance" not in column and "ratio" not in column]
    volume_columns = [column for column in FEATURE_COLUMNS if ("volume" in column or "size" in column) and "imbalance" not in column and "ratio" not in column]
    ratio_columns = [column for column in FEATURE_COLUMNS if "ratio" in column or "imbalance" in column]
    negative_counts = int((frame[count_columns] < 0).sum().sum())
    negative_volumes = int((frame[volume_columns] < 0).sum().sum())
    ratio_out_of_bounds = int(((frame[ratio_columns] < -1.000001) | (frame[ratio_columns] > 1.000001)).sum().sum())
    expected_start = pd.Timestamp(TARGET_WINDOW_START, tz="UTC")
    expected_end = pd.Timestamp(TARGET_WINDOW_END, tz="UTC") + pd.Timedelta(days=1)
    coverage_ok = frame["open_ts"].iloc[0] == expected_start and frame["close_ts"].iloc[-1] == expected_end
    quality_ok = (
        len(frame) == expected_rows
        and duplicate_close_ts == 0
        and bool(frame["open_ts"].is_monotonic_increasing)
        and leakage_violations == 0
        and not forbidden
        and feature_null_count == 0
        and invalid_rows == 0
        and negative_counts == 0
        and negative_volumes == 0
        and ratio_out_of_bounds == 0
    )
    return {
        "version": VERSION,
        "timeframe": timeframe,
        "output_path": output_path.as_posix(),
        "expected_rows": expected_rows,
        "actual_rows": int(len(frame)),
        "coverage_start": str(frame["open_ts"].iloc[0]) if len(frame) else None,
        "coverage_end": str(frame["close_ts"].iloc[-1]) if len(frame) else None,
        "days_expected": EXPECTED_DAYS,
        "days_complete": EXPECTED_DAYS if coverage_ok and len(frame) == expected_rows else 0,
        "days_missing": 0 if coverage_ok and len(frame) == expected_rows else EXPECTED_DAYS,
        "duplicate_event_ts_or_close_ts": duplicate_close_ts,
        "timestamps_monotone": bool(frame["open_ts"].is_monotonic_increasing),
        "feature_available_ts_le_decision_ts": leakage_violations == 0,
        "forbidden_columns": forbidden,
        "exact_feature_null_count": feature_null_count,
        "exact_feature_error_count": int(frame["exact_feature_error_count"].sum()),
        "no_trade_bucket_count": int(frame["no_trade_bucket"].sum()),
        "aggtrades_missing_flag_count": int(frame["aggtrades_missing_flag"].sum()),
        "partial_bucket_flag_count": int(frame["aggtrades_partial_bucket_flag"].sum()),
        "range_summary": {
            "negative_counts": negative_counts,
            "negative_volumes": negative_volumes,
            "ratio_out_of_bounds": ratio_out_of_bounds,
        },
        "quality_status": "PASS" if quality_ok else "FAIL",
        "coverage_status": "PASS" if coverage_ok and len(frame) == expected_rows else "FAIL",
    }


def build_global_report_v9_45(*, root: Path, run_id: str, preflight: dict[str, Any], inputs: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]], output_paths: dict[str, Path], runtime_seconds: float, created: bool) -> dict[str, Any]:
    coverage_pass = set(timeframe_reports) == set(EXPECTED_TIMEFRAMES) and all(item["coverage_status"] == "PASS" for item in timeframe_reports.values())
    quality_pass = coverage_pass and all(item["quality_status"] == "PASS" for item in timeframe_reports.values())
    leakage_guard = {"status": "PASS" if all(item.get("feature_available_ts_le_decision_ts") for item in timeframe_reports.values()) else "FAIL", "feature_available_ts_le_decision_ts": all(item.get("feature_available_ts_le_decision_ts") for item in timeframe_reports.values()), "rolling_windows_past_only": True, "new_labels_created": False}
    forbidden_scan = {"status": "PASS" if all(not item.get("forbidden_columns") for item in timeframe_reports.values()) else "FAIL", "forbidden_columns": {tf: item.get("forbidden_columns", []) for tf, item in timeframe_reports.items()}}
    decision = decide_v9_45(preflight, created, quality_pass, leakage_guard, forbidden_scan, timeframe_reports)
    row_counts = {timeframe: report["actual_rows"] for timeframe, report in timeframe_reports.items()}
    output_sizes = {timeframe: (output_paths[timeframe].stat().st_size if output_paths[timeframe].is_file() else 0) for timeframe in EXPECTED_TIMEFRAMES}
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "source_aggtrades_validation_version": SOURCE_AGGTRADES_VALIDATION_VERSION,
        "created_at_utc": _utc_now(),
        "feature_run_id": run_id,
        "direction": DIRECTION,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "days_expected": EXPECTED_DAYS},
        "timeframes": list(EXPECTED_TIMEFRAMES),
        "processing_strategy": preflight["processing_strategy"],
        "chunking_strategy": preflight["chunking_strategy"],
        "disk_preflight": preflight,
        "input_versions": {name: payload.get("version") for name, payload in inputs.items() if isinstance(payload, dict)},
        "feature_store_created": decision in {"aggtrades_exact_5y_feature_enrichment_created", "aggtrades_exact_5y_feature_enrichment_created_with_warnings"},
        "features_created": decision in {"aggtrades_exact_5y_feature_enrichment_created", "aggtrades_exact_5y_feature_enrichment_created_with_warnings"},
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "feature_paths": {timeframe: path.as_posix() for timeframe, path in output_paths.items()},
        "output_bytes": output_sizes,
        "row_counts": row_counts,
        "feature_columns": list(FEATURE_COLUMNS),
        "feature_columns_count": len(FEATURE_COLUMNS),
        "feature_families": FEATURE_FAMILIES,
        "timeframe_reports": timeframe_reports,
        "null_summary": {timeframe: item["exact_feature_null_count"] for timeframe, item in timeframe_reports.items()},
        "range_summary": {timeframe: item["range_summary"] for timeframe, item in timeframe_reports.items()},
        "no_trade_summary": {timeframe: item["no_trade_bucket_count"] for timeframe, item in timeframe_reports.items()},
        "leakage_guard": leakage_guard,
        "forbidden_column_scan": forbidden_scan,
        "quality_status": "PASS" if quality_pass else "FAIL",
        "coverage_status": "target_5y_exact_feature_window_complete" if coverage_pass else "target_5y_exact_feature_window_incomplete",
        "limitations": [
            "V9.45 cree une couche separee et ne modifie pas le feature store V9.37.",
            "Les quantiles sont calcules sur le bucket courant termine; ils ne lisent pas les buckets futurs.",
            "Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal n'est produit.",
        ],
        "warnings": build_warnings_v9_45(preflight, timeframe_reports, decision),
        "decision": decision,
        "next_recommendation": "V9.46 - AggTrades Exact 5Y Feature Enrichment Validation" if decision in {"aggtrades_exact_5y_feature_enrichment_created", "aggtrades_exact_5y_feature_enrichment_created_with_warnings"} else "V9.46 - Exact Feature Enrichment Correction",
        "runtime_seconds": runtime_seconds,
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }


def build_preflight_v9_45(root: Path) -> dict[str, Any]:
    data_path = root / "data"
    usage = shutil.disk_usage(data_path if data_path.exists() else root)
    free_gib = usage.free / (1024**3)
    silver_size = _directory_size(root / "data/silver/public_trades")
    base_feature_size = _directory_size(root / "data/research/v9_37/features/ohlcv_aggtrades_5y")
    estimated_output_size_gib = max(2.0, base_feature_size / (1024**3) * 1.6)
    return {
        "free_gib_data_mount": round(free_gib, 3),
        "free_gib_project_mount": round(shutil.disk_usage(root).free / (1024**3), 3),
        "silver_public_trades_size_gib": round(silver_size / (1024**3), 3),
        "v9_37_feature_store_size_gib": round(base_feature_size / (1024**3), 3),
        "estimated_output_size_gib": round(estimated_output_size_gib, 3),
        "safe_to_run_exact_enrichment": free_gib >= 50.0,
        "processing_strategy": "parallel_daily_partitioned_aggtrades_scan_then_timeframe_concat",
        "chunking_strategy": "read one daily silver parquet per worker; default bounded parallelism is 12 workers via GALAPAGOS_V9_45_WORKERS",
        "storage_warning": free_gib < 80.0,
        "runtime_warning": True,
    }


def build_manifest_v9_45(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "target_window": report["target_window"],
        "timeframes": report["timeframes"],
        "feature_paths": report["feature_paths"],
        "reports": [REPORT_JSON_PATH.as_posix(), REPORT_MD_PATH.as_posix(), DOC_PATH.as_posix()],
        "timeframe_reports": [timeframe_report_path_v9_45(tf).as_posix() for tf in EXPECTED_TIMEFRAMES],
        "feature_columns_count": report["feature_columns_count"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }


def build_markdown_v9_45(report: dict[str, Any]) -> str:
    lines = [
        "# Enrichissement features exactes aggTrades V9.45",
        "",
        f"- Decision : `{report['decision']}`.",
        f"- Recommandation : `{report['next_recommendation']}`.",
        f"- Fenetre : `{TARGET_WINDOW_START}` -> `{TARGET_WINDOW_END}`.",
        f"- Timeframes : `{report['timeframes']}`.",
        f"- Strategie : `{report['processing_strategy']}`.",
        f"- Chunking : `{report['chunking_strategy']}`.",
        f"- Feature columns : `{report['feature_columns_count']}`.",
        f"- Row counts : `{report['row_counts']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Coverage : `{report['coverage_status']}`.",
        f"- Leakage guard : `{report['leakage_guard']['status']}`.",
        f"- Forbidden columns scan : `{report['forbidden_column_scan']['status']}`.",
        "",
        "## Sorties",
        "",
    ]
    for timeframe, path in report["feature_paths"].items():
        lines.append(f"- `{timeframe}` : `{path}`.")
    lines.extend(
        [
            "",
            "## Garde-fous",
            "",
            "- Aucun trading.",
            "- Aucun paper live.",
            "- Aucun ordre.",
            "- Aucun backtest.",
            "- Aucun walk-forward.",
            "- Aucun ML.",
            "- Aucun dataset supervise.",
            "- Aucun label cree.",
            "- Aucune strategie.",
            "- Aucun signal actionnable.",
            "- Aucun modele persistant.",
            "- Aucun reseau.",
            "- Aucun telechargement de nouvelles donnees.",
            "- Aucune suppression destructive.",
            "- Aucun sidecar et aucune empreinte ZIP.",
            "",
        ]
    )
    return "\n".join(lines)


def update_state_surfaces_v9_45(root: Path, report: dict[str, Any]) -> None:
    latest_path = root / "reports/current/latest_metrics.json"
    latest = _read_optional_json(latest_path)
    latest.update(
        {
            "last_validated_version": LAST_VALIDATED_VERSION,
            "candidate_version": VERSION,
            "candidate_status": "pending_external_audit",
            "direction": DIRECTION,
            "quality_status": report["quality_status"],
            "coverage_status": report["coverage_status"],
            "decision_v9_45": report["decision"],
            "aggtrades_exact_v9_45_feature_columns_count": report["feature_columns_count"],
            "aggtrades_exact_v9_45_row_counts": report["row_counts"],
            "recommended_next_step": report["next_recommendation"],
            "features_created": report["features_created"],
            "dataset_created": False,
            "ml_executed": False,
            "labels_created": False,
            **SAFETY_FLAGS,
        }
    )
    _write_json(latest_path, latest)
    _write_text(root / "reports/current/latest_metrics.md", "# Latest Metrics\n\n" f"- Version candidate : `{VERSION}`.\n" f"- Decision V9.45 : `{report['decision']}`.\n" f"- Feature columns : `{report['feature_columns_count']}`.\n" f"- Row counts : `{report['row_counts']}`.\n" "- Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.\n")
    _write_text(root / "reports/current/latest_summary.md", "# Synthese courante\n\n" f"V9.45 cree une couche de features exactes aggTrades 5Y separee du feature store V9.37. Decision : `{report['decision']}`. Recommandation : `{report['next_recommendation']}`.\n")
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_optional_json(state_path)
    state.update({"last_validated_version": LAST_VALIDATED_VERSION, "candidate_version": VERSION, "candidate_status": "pending_external_audit", "direction": DIRECTION, "decision_v9_45": report["decision"], "features_created_v9_45": report["features_created"], **FINDINGS, **SAFETY_FLAGS})
    _write_json(state_path, state)
    _write_text(root / "reports/PROJECT_STATE.md", "# Etat Projet Galapagos\n\n" f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n" f"- Version candidate : `{VERSION}`.\n" "- Statut candidat : `pending_external_audit`.\n" f"- Direction : `{DIRECTION}`.\n" f"- Decision : `{report['decision']}`.\n" f"- Recommandation : `{report['next_recommendation']}`.\n" "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, label, strategie, signal, modele persistant, API privee, cle API, reseau ou telechargement.\n")
    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else "# Projet Galapagos\n"
    marker = "## V9.45 - AggTrades Exact Feature Enrichment"
    if marker not in readme:
        _write_text(root / "README.md", readme.rstrip() + "\n\n" + marker + "\n\n" f"- Decision : `{report['decision']}`.\n" f"- Recommandation : `{report['next_recommendation']}`.\n" "- Feature-enrichment-only : aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.\n")


def decide_v9_45(preflight: dict[str, Any], created: bool, quality_pass: bool, leakage_guard: dict[str, Any], forbidden_scan: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]]) -> str:
    if not preflight["safe_to_run_exact_enrichment"]:
        return "aggtrades_exact_5y_feature_enrichment_blocked_by_storage"
    if not created:
        return "aggtrades_exact_5y_feature_enrichment_blocked_by_runtime"
    if leakage_guard["status"] != "PASS":
        return "aggtrades_exact_5y_feature_enrichment_blocked_by_leakage"
    if forbidden_scan["status"] != "PASS" or not quality_pass:
        if any(item.get("actual_rows", 0) > 0 for item in timeframe_reports.values()):
            return "aggtrades_exact_5y_feature_enrichment_partial"
        return "aggtrades_exact_5y_feature_enrichment_blocked_by_quality"
    if preflight["storage_warning"] or preflight["runtime_warning"]:
        return "aggtrades_exact_5y_feature_enrichment_created_with_warnings"
    return "aggtrades_exact_5y_feature_enrichment_created"


def build_warnings_v9_45(preflight: dict[str, Any], timeframe_reports: dict[str, dict[str, Any]], decision: str) -> list[str]:
    warnings: list[str] = []
    if preflight["storage_warning"]:
        warnings.append("Espace disque sous 80 GiB; calcul autorise car au-dessus du seuil bloquant 50 GiB.")
    if preflight["runtime_warning"]:
        warnings.append("Calcul exact long: scan partitionne de tous les jours aggTrades silver 5Y.")
    if decision.endswith("_with_warnings"):
        warnings.append("Les warnings runtime/stockage sont non bloquants.")
    for timeframe, report in timeframe_reports.items():
        if report.get("no_trade_bucket_count", 0) > 0:
            warnings.append(f"{timeframe}: buckets sans trade conserves avec zeros et no_trade_bucket=1.")
    return warnings


def exact_feature_output_path_v9_45(root: Path, timeframe: str) -> Path:
    return root / f"data/research/v9_45/features/aggtrades_exact_5y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2021-05-05_2026-05-05/features.parquet"


def timeframe_report_path_v9_45(timeframe: str) -> Path:
    return Path(f"reports/features/aggtrades_exact_5y_feature_enrichment_{timeframe}_v9_45.json")


def silver_aggtrades_path_v9_45(root: Path, day: date) -> Path:
    return root / f"data/silver/public_trades/venue=binance/market_type=spot/symbol=BTCUSDT/date={day.isoformat()}/agg_trades.parquet"


def _large_trade_features(frame: pd.DataFrame) -> pd.DataFrame:
    thresholds = frame.groupby("bucket_start", observed=True)["quantity"].quantile([0.95, 0.99]).unstack()
    thresholds.columns = ["p95_threshold", "p99_threshold"]
    work = frame.join(thresholds, on="bucket_start")
    work["is_large_p95"] = work["quantity"] >= work["p95_threshold"]
    work["is_large_p99"] = work["quantity"] >= work["p99_threshold"]
    work["large_volume_p95"] = np.where(work["is_large_p95"], work["quantity"], 0.0)
    work["large_volume_p99"] = np.where(work["is_large_p99"], work["quantity"], 0.0)
    return work.groupby("bucket_start", observed=True).agg(
        large_trade_count_p95_exact=("is_large_p95", "sum"),
        large_trade_volume_p95_exact=("large_volume_p95", "sum"),
        large_trade_count_p99_exact=("is_large_p99", "sum"),
        large_trade_volume_p99_exact=("large_volume_p99", "sum"),
    )


def _trade_size_bucket_counts(frame: pd.DataFrame) -> pd.DataFrame:
    conditions = [
        frame["quantity"] < 0.01,
        (frame["quantity"] >= 0.01) & (frame["quantity"] < 0.1),
        (frame["quantity"] >= 0.1) & (frame["quantity"] < 1.0),
        frame["quantity"] >= 1.0,
    ]
    labels = ["small", "medium", "large", "whale"]
    work = frame[["bucket_start"]].copy()
    work["bucket"] = np.select(conditions, labels, default="small")
    counts = pd.crosstab(work["bucket_start"], work["bucket"])
    for label in labels:
        column = f"trade_size_bucket_{label}_count"
        counts[column] = counts[label] if label in counts.columns else 0
    return counts[[f"trade_size_bucket_{label}_count" for label in labels]]


def _safe_ratio(numerator: Any, denominator: Any) -> Any:
    numerator_series = pd.Series(numerator)
    denominator_series = pd.Series(denominator).replace(0, np.nan)
    return (numerator_series / denominator_series).replace([np.inf, -np.inf], 0.0).fillna(0.0).to_numpy()


def _pandas_freq(timeframe: str) -> str:
    return {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}[timeframe]


def _timeframe_seconds(timeframe: str) -> int:
    return {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}[timeframe]


def _date_range(start: date, end: date) -> list[date]:
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _sources_ready(inputs: dict[str, Any]) -> bool:
    return inputs.get("v9_32_aggtrades_validation", {}).get("quality_status") == "PASS" and inputs.get("v9_44_diagnostic", {}).get("decision") == "feature_enrichment_before_more_ml"


def _blocked_timeframe_report(timeframe: str, preflight: dict[str, Any]) -> dict[str, Any]:
    return {"version": VERSION, "timeframe": timeframe, "expected_rows": EXPECTED_ROWS_BY_TIMEFRAME[timeframe], "actual_rows": 0, "coverage_start": None, "coverage_end": None, "days_expected": EXPECTED_DAYS, "days_complete": 0, "days_missing": EXPECTED_DAYS, "duplicate_event_ts_or_close_ts": 0, "timestamps_monotone": False, "feature_available_ts_le_decision_ts": False, "forbidden_columns": [], "exact_feature_null_count": 0, "exact_feature_error_count": 0, "no_trade_bucket_count": 0, "aggtrades_missing_flag_count": 0, "partial_bucket_flag_count": 0, "range_summary": {}, "quality_status": "FAIL", "coverage_status": "FAIL", "preflight": preflight}


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
