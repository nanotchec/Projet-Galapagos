from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galapagos.data.public_market.max_history_window import MANIFEST_PATH_V5_0
from galapagos.data.public_market.max_history_window_validation import validate_max_history_public_market_data_v5_0
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso
from galapagos.data.public_market.storage import read_parquet, write_parquet
from galapagos.data.public_trades.expanded_window_validation import validate_public_trades_expanded_window_v7_1
from galapagos.features.ohlcv_trades_quality import assess_ohlcv_trades_feature_quality_v7_2
from galapagos.features.ohlcv_trades_schemas import (
    OHLCV_TRADES_FEATURE_COLUMNS_V7_2,
    OHLCV_TRADES_VALUE_COLUMNS_V7_2,
)


VERSION_V7_2 = "V7.2"
FEATURE_SCHEMA_VERSION_V7_2 = "OHLCV_TRADES_FEATURE_COLUMNS_V7_2"
TIMEFRAMES_V7_2 = ["1m", "5m", "15m", "1h"]
EXPECTED_ROWS_V7_2 = {"1m": 43200, "5m": 8640, "15m": 2880, "1h": 720}
TIMEFRAME_MINUTES_V7_2 = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}
V7_1_TRADES_MANIFEST_PATH = Path("reports/manifests/public_trades_expanded_window_v7_1_manifest.json")
MANIFEST_PATH_V7_2 = Path("reports/manifests/ohlcv_trades_feature_store_v7_2_manifest.json")
REPORT_JSON_PATH_V7_2 = Path("reports/features/ohlcv_trades_feature_store_v7_2.json")
REPORT_MD_PATH_V7_2 = Path("reports/features/ohlcv_trades_feature_store_v7_2.md")
DOC_PATH_V7_2 = Path("docs/ohlcv_trades_feature_store_v7_2.md")
WINDOW_START_V7_2 = "2023-03-25"
WINDOW_END_V7_2 = "2023-04-23"
TOTAL_DAYS_V7_2 = 30
LARGE_TRADE_QUOTE_THRESHOLD_V7_2 = 100_000.0
EXPECTED_LIMITATIONS_V7_2 = [
    "V7.2 produit uniquement des features causales OHLCV + aggTrades sur une fenetre bornee de 30 jours.",
    "V7.2 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]


def run_ohlcv_trades_feature_store_v7_2(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    project_root = root.resolve()
    if validate_inputs:
        v5_validation = validate_max_history_public_market_data_v5_0(project_root)
        if not v5_validation["passed"]:
            raise RuntimeError(f"V5.0 validation failed before V7.2: {v5_validation['errors']}")
        v7_1_validation = validate_public_trades_expanded_window_v7_1(project_root)
        if not v7_1_validation["passed"]:
            raise RuntimeError(f"V7.1 validation failed before V7.2: {v7_1_validation['errors']}")

    v5_manifest = load_v5_0_ohlcv_manifest(project_root)
    trades_manifest = load_v7_1_trades_manifest(project_root)
    _validate_input_manifests(v5_manifest, trades_manifest)

    created_at = utc_now_iso()
    feature_run_id = f"v7_2_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    trades_manifest_sha = sha256_file(project_root / V7_1_TRADES_MANIFEST_PATH)
    trade_aggregates = build_trade_aggregates_by_timeframe(project_root, trades_manifest)

    input_ohlcv: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V7_2:
        input_path = input_ohlcv_path(project_root, timeframe, v5_manifest)
        input_sha = sha256_file(input_path)
        ohlcv = read_parquet(input_path)
        ohlcv_window = filter_ohlcv_to_v7_2_window(ohlcv)
        feature_frame = build_ohlcv_trades_features_v7_2(
            ohlcv_window,
            trade_aggregates[timeframe],
            timeframe,
            source_ohlcv_sha256=input_sha,
            source_trades_manifest_sha256=trades_manifest_sha,
            feature_run_id=feature_run_id,
        )
        output = output_path(project_root, timeframe, WINDOW_START_V7_2, WINDOW_END_V7_2)
        write_parquet(feature_frame[OHLCV_TRADES_FEATURE_COLUMNS_V7_2], output)
        input_ohlcv[timeframe] = {
            "path": input_path.relative_to(project_root).as_posix(),
            "sha256": input_sha,
            "rows": int(len(ohlcv_window)),
        }
        outputs[timeframe] = {
            "path": output.relative_to(project_root).as_posix(),
            "sha256": sha256_file(output),
            "bytes": output.stat().st_size,
            "rows": int(len(feature_frame)),
            "format": "parquet",
        }
        quality[timeframe] = assess_ohlcv_trades_feature_quality_v7_2(
            feature_frame,
            timeframe,
            expected_rows=EXPECTED_ROWS_V7_2[timeframe],
        )
        quality[timeframe]["source_hashes_valid"] = True
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V7_2,
        "status": status,
        "created_at_utc": created_at,
        "feature_run_id": feature_run_id,
        "input_ohlcv_manifest": {
            "path": MANIFEST_PATH_V5_0.as_posix(),
            "sha256": sha256_file(project_root / MANIFEST_PATH_V5_0),
            "source_window_start": v5_manifest["discovery"]["window_start"],
            "source_window_end": v5_manifest["discovery"]["window_end"],
        },
        "input_trades_manifest": {
            "path": V7_1_TRADES_MANIFEST_PATH.as_posix(),
            "sha256": trades_manifest_sha,
            "window_start": trades_manifest["discovery"]["window_start"],
            "window_end": trades_manifest["discovery"]["window_end"],
            "total_days": trades_manifest["discovery"]["total_days"],
            "trade_source_type": trades_manifest["source"]["trade_source_type"],
        },
        "window": {
            "window_start": WINDOW_START_V7_2,
            "window_end": WINDOW_END_V7_2,
            "total_days": TOTAL_DAYS_V7_2,
            "bucket_convention": "[event_ts, next_event_ts), equivalent to [event_ts, close_ts] for millisecond klines",
        },
        "input_ohlcv": input_ohlcv,
        "input_trades": {
            "path_or_partitions": trades_manifest["outputs"]["partitions"],
            "rows": trades_manifest["outputs"]["total_rows"],
            "sha256_or_partition_hashes": {
                date_key: payload["sha256"] for date_key, payload in trades_manifest["outputs"]["partitions"].items()
            },
        },
        "outputs": outputs,
        "feature_schema_version": FEATURE_SCHEMA_VERSION_V7_2,
        "feature_columns": OHLCV_TRADES_FEATURE_COLUMNS_V7_2,
        "quality": quality,
        "safety": safety_flags_v7_2(),
        "limitations": EXPECTED_LIMITATIONS_V7_2,
    }
    report = build_report_v7_2(manifest)
    _write_json(project_root / MANIFEST_PATH_V7_2, manifest)
    _write_json(project_root / REPORT_JSON_PATH_V7_2, report)
    markdown = build_ohlcv_trades_feature_store_markdown_v7_2(report)
    _write_text(project_root / REPORT_MD_PATH_V7_2, markdown)
    _write_text(project_root / DOC_PATH_V7_2, markdown)
    update_project_state_v7_2(project_root, manifest)
    return manifest


def build_trade_aggregates_by_timeframe(root: Path, trades_manifest: dict[str, Any]) -> dict[str, pd.DataFrame]:
    aggregated: dict[str, list[pd.DataFrame]] = {timeframe: [] for timeframe in TIMEFRAMES_V7_2}
    for _date_key, payload in sorted(trades_manifest["outputs"]["partitions"].items()):
        partition = read_parquet(root / payload["path"])
        partition = partition[["price", "quantity", "trade_ts", "is_buyer_maker"]].copy()
        partition["trade_ts"] = pd.to_datetime(partition["trade_ts"], utc=True)
        partition["price"] = partition["price"].astype("float64")
        partition["quantity"] = partition["quantity"].astype("float64")
        partition["quote_quantity"] = partition["price"] * partition["quantity"]
        partition["is_taker_buy"] = ~partition["is_buyer_maker"].astype(bool)
        partition["is_large_trade"] = partition["quote_quantity"] >= LARGE_TRADE_QUOTE_THRESHOLD_V7_2
        for timeframe in TIMEFRAMES_V7_2:
            aggregated[timeframe].append(_aggregate_trade_partition(partition, timeframe))
    return {
        timeframe: pd.concat(frames, ignore_index=True).sort_values("event_ts").reset_index(drop=True)
        for timeframe, frames in aggregated.items()
    }


def build_ohlcv_trades_features_v7_2(
    ohlcv: pd.DataFrame,
    trade_aggregates: pd.DataFrame,
    timeframe: str,
    *,
    source_ohlcv_sha256: str,
    source_trades_manifest_sha256: str,
    feature_run_id: str,
) -> pd.DataFrame:
    frame = ohlcv.sort_values("event_ts").reset_index(drop=True).copy()
    frame["event_ts"] = pd.to_datetime(frame["event_ts"], utc=True)
    for column in ["close_ts", "available_ts", "decision_ts"]:
        frame[column] = pd.to_datetime(frame[column], utc=True)

    renamed = frame.rename(
        columns={
            "trade_count": "trade_count_ohlcv",
            "taker_buy_base_volume": "taker_buy_base_volume_ohlcv",
            "taker_buy_quote_volume": "taker_buy_quote_volume_ohlcv",
        }
    )
    aggregates = trade_aggregates.copy()
    aggregates["event_ts"] = pd.to_datetime(aggregates["event_ts"], utc=True)
    merged = renamed.merge(aggregates, on="event_ts", how="left", validate="one_to_one")
    merged = _fill_missing_trade_buckets(merged)
    features = _derive_feature_columns(merged, timeframe)
    features["feature_run_id"] = feature_run_id
    features["source_ohlcv_sha256"] = source_ohlcv_sha256
    features["source_trades_manifest_sha256"] = source_trades_manifest_sha256
    features["trade_source_type"] = "aggTrades"
    features["feature_schema_version"] = FEATURE_SCHEMA_VERSION_V7_2
    features["feature_available_ts"] = features["available_ts"]

    audit_basis = [column for column in OHLCV_TRADES_VALUE_COLUMNS_V7_2 if column not in {"trades_feature_null_count", "trades_feature_error_count"}]
    features["warmup_row"] = _warmup_mask(features)
    features["trades_feature_null_count"] = features[audit_basis].isna().sum(axis=1).astype("int64")
    features["trades_feature_error_count"] = _row_error_count(features)
    return features[OHLCV_TRADES_FEATURE_COLUMNS_V7_2]


def filter_ohlcv_to_v7_2_window(ohlcv: pd.DataFrame) -> pd.DataFrame:
    frame = ohlcv.copy()
    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    start = pd.Timestamp(f"{WINDOW_START_V7_2}T00:00:00Z")
    end_exclusive = pd.Timestamp(f"{pd.Timestamp(WINDOW_END_V7_2) + pd.Timedelta(days=1):%Y-%m-%d}T00:00:00Z")
    return frame.loc[(event_ts >= start) & (event_ts < end_exclusive)].reset_index(drop=True)


def load_v5_0_ohlcv_manifest(root: Path) -> dict[str, Any]:
    return _read_json(root / MANIFEST_PATH_V5_0)


def load_v7_1_trades_manifest(root: Path) -> dict[str, Any]:
    return _read_json(root / V7_1_TRADES_MANIFEST_PATH)


def input_ohlcv_path(root: Path, timeframe: str, manifest: dict[str, Any]) -> Path:
    return root / manifest["outputs"][timeframe]["path"]


def output_path(root: Path, timeframe: str, window_start: str, window_end: str) -> Path:
    return (
        root
        / "data/research/v7_2/features/ohlcv_trades"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "features.parquet"
    )


def build_report_v7_2(manifest: dict[str, Any]) -> dict[str, Any]:
    return dict(manifest)


def build_ohlcv_trades_feature_store_markdown_v7_2(report: dict[str, Any]) -> str:
    output_rows = "\n".join(
        f"- `{timeframe}` : `{payload['path']}`, `{payload['rows']}` lignes, checksum `{payload['sha256']}`"
        for timeframe, payload in report["outputs"].items()
    )
    quality_rows = "\n".join(
        f"- `{timeframe}` : warmup `{payload['warmup_rows']}`, bougies sans trades `{payload['bars_without_trades']}`, "
        f"diff volume mediane `{payload['median_volume_relative_diff']}`, diff quote mediane `{payload['median_quote_volume_relative_diff']}`"
        for timeframe, payload in report["quality"].items()
    )
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    return f"""# Feature Store OHLCV + Trades V7.2

## Objectif

V7.2 produit uniquement des features causales de recherche OHLCV + aggTrades sur la fenetre bornee V7.1.

## Fenetre

- Fenetre : `{report['window']['window_start']}` -> `{report['window']['window_end']}`.
- Total jours : `{report['window']['total_days']}`.
- Convention bougie/trades : `{report['window']['bucket_convention']}`.
- Source trades : `{report['input_trades_manifest']['trade_source_type']}`.

## Outputs

{output_rows}

## Qualite

{quality_rows}

## Limitations

{limitations}

## Securite

V7.2 ne valide aucune strategie.
V7.2 ne produit aucun label.
V7.2 ne produit aucun dataset ML.
V7.2 ne produit aucun modele ML.
V7.2 ne produit aucun backtest.
V7.2 ne produit aucun signal de trading.
V7.2 ne produit aucun ordre.
V7.2 n'autorise aucun paper live.
V7.2 n'autorise aucun trading reel.
Les features trades sont des variables de recherche, pas des signaux.
"""


def safety_flags_v7_2() -> dict[str, bool]:
    return {
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "ml_enabled": False,
        "labels_enabled": False,
        "dataset_enabled": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
    }


def update_project_state_v7_2(root: Path, manifest: dict[str, Any]) -> None:
    project_state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(project_state_path) if project_state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V7.1",
            "candidate_version": "V7.2",
            "candidate_status": "pending_external_audit",
            "direction": "OHLCV + public trades feature store preview",
            "ohlcv_trades_features_v7_2_created": True,
            "labels_v7_2_created": False,
            "dataset_v7_2_created": False,
            "ml_v7_2_created": False,
            "model_v7_2_created": False,
            "backtest_v7_2_created": False,
            "strategy_v7_2_created": False,
            "orders_v7_2_created": False,
            "window_start_v7_2": manifest["window"]["window_start"],
            "window_end_v7_2": manifest["window"]["window_end"],
            "total_days_v7_2": manifest["window"]["total_days"],
            "trade_source_type_v7_2": manifest["input_trades_manifest"]["trade_source_type"],
            "feature_columns_v7_2_count": len(manifest["feature_columns"]),
            "output_rows_v7_2": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()},
            "backtest_enabled": False,
            "strategy_enabled": False,
            "paper_live_enabled": False,
            "orders_enabled": False,
            "trading_enabled": False,
            "execution_enabled": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "authentication_used": False,
            "external_validation_required": True,
        }
    )
    _write_json(project_state_path, state)
    _write_current_reports(root, manifest)


def _aggregate_trade_partition(partition: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    frequency = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}[timeframe]
    working = partition.copy()
    working["event_ts"] = working["trade_ts"].dt.floor(frequency)
    working["taker_buy_quantity_part"] = np.where(working["is_taker_buy"], working["quantity"], 0.0)
    working["taker_sell_quantity_part"] = np.where(~working["is_taker_buy"], working["quantity"], 0.0)
    working["taker_buy_quote_part"] = np.where(working["is_taker_buy"], working["quote_quantity"], 0.0)
    working["taker_sell_quote_part"] = np.where(~working["is_taker_buy"], working["quote_quantity"], 0.0)
    working["large_quantity_part"] = np.where(working["is_large_trade"], working["quantity"], 0.0)
    grouped = working.groupby("event_ts", sort=True)
    result = grouped.agg(
        agg_trade_count=("price", "size"),
        agg_trade_quantity_sum=("quantity", "sum"),
        agg_trade_quote_quantity_sum=("quote_quantity", "sum"),
        agg_trade_price_min=("price", "min"),
        agg_trade_price_max=("price", "max"),
        agg_trade_price_mean=("price", "mean"),
        agg_trade_price_std=("price", "std"),
        agg_trade_first_price=("price", "first"),
        agg_trade_last_price=("price", "last"),
        agg_trade_quantity_mean=("quantity", "mean"),
        agg_trade_quantity_std=("quantity", "std"),
        agg_trade_quantity_max=("quantity", "max"),
        agg_trade_large_trade_count=("is_large_trade", "sum"),
        agg_trade_large_trade_quantity_sum=("large_quantity_part", "sum"),
        taker_buy_agg_count=("is_taker_buy", "sum"),
        taker_buy_quantity=("taker_buy_quantity_part", "sum"),
        taker_sell_quantity=("taker_sell_quantity_part", "sum"),
        taker_buy_quote_quantity=("taker_buy_quote_part", "sum"),
        taker_sell_quote_quantity=("taker_sell_quote_part", "sum"),
    ).reset_index()
    result["taker_sell_agg_count"] = result["agg_trade_count"] - result["taker_buy_agg_count"]
    return result


def _fill_missing_trade_buckets(frame: pd.DataFrame) -> pd.DataFrame:
    zero_columns = [
        "agg_trade_count",
        "agg_trade_quantity_sum",
        "agg_trade_quote_quantity_sum",
        "agg_trade_large_trade_count",
        "agg_trade_large_trade_quantity_sum",
        "taker_buy_agg_count",
        "taker_sell_agg_count",
        "taker_buy_quantity",
        "taker_sell_quantity",
        "taker_buy_quote_quantity",
        "taker_sell_quote_quantity",
    ]
    for column in zero_columns:
        frame[column] = frame[column].fillna(0.0)
    for column in ["agg_trade_price_std", "agg_trade_quantity_std"]:
        frame[column] = frame[column].fillna(0.0)
    return frame


def _derive_feature_columns(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    features = frame.copy()
    count = features["agg_trade_count"].astype("float64")
    quantity = features["agg_trade_quantity_sum"].astype("float64")
    quote_quantity = features["agg_trade_quote_quantity_sum"].astype("float64")
    first_price = features["agg_trade_first_price"].astype("float64")
    last_price = features["agg_trade_last_price"].astype("float64")
    price_min = features["agg_trade_price_min"].astype("float64")
    price_max = features["agg_trade_price_max"].astype("float64")

    features["agg_trade_vwap"] = _safe_div(quote_quantity, quantity)
    features["agg_trade_price_change"] = last_price - first_price
    features["agg_trade_price_return"] = _safe_div(last_price, first_price) - 1.0
    features["taker_buy_ratio_count"] = _safe_div(features["taker_buy_agg_count"], count)
    features["taker_buy_ratio_quantity"] = _safe_div(features["taker_buy_quantity"], quantity)
    features["taker_buy_ratio_quote"] = _safe_div(features["taker_buy_quote_quantity"], quote_quantity)
    features["taker_imbalance_count"] = _safe_div(features["taker_buy_agg_count"] - features["taker_sell_agg_count"], count)
    features["taker_imbalance_quantity"] = _safe_div(
        features["taker_buy_quantity"] - features["taker_sell_quantity"], quantity
    )
    features["taker_imbalance_quote"] = _safe_div(
        features["taker_buy_quote_quantity"] - features["taker_sell_quote_quantity"], quote_quantity
    )
    minutes = TIMEFRAME_MINUTES_V7_2[timeframe]
    features["agg_trades_per_minute"] = count / minutes
    features["agg_quantity_per_minute"] = quantity / minutes
    features["agg_quote_quantity_per_minute"] = quote_quantity / minutes
    features["avg_agg_trades_per_ohlcv_trade"] = _safe_div(count, features["trade_count_ohlcv"])
    features["agg_trade_count_vs_ohlcv_trade_count_ratio"] = _safe_div(count, features["trade_count_ohlcv"])
    features["agg_quantity_vs_ohlcv_volume_ratio"] = _safe_div(quantity, features["volume"])
    features["agg_quote_vs_ohlcv_quote_volume_ratio"] = _safe_div(quote_quantity, features["quote_volume"])

    for column, source in [
        ("agg_trade_count", count),
        ("agg_quantity", quantity),
        ("taker_buy_ratio_quantity", features["taker_buy_ratio_quantity"]),
        ("taker_imbalance_quantity", features["taker_imbalance_quantity"]),
    ]:
        if column in {"agg_trade_count"}:
            features[f"{column}_lag_1"] = source.shift(1)
            for window in [5, 15, 60]:
                features[f"{column}_rolling_mean_{window}"] = source.rolling(window, min_periods=window).mean()
            features[f"{column}_zscore_60"] = _rolling_zscore(source, 60)
        elif column == "agg_quantity":
            for window in [5, 15, 60]:
                features[f"{column}_rolling_mean_{window}"] = source.rolling(window, min_periods=window).mean()
            features[f"{column}_zscore_60"] = _rolling_zscore(source, 60)
        else:
            features[f"{column}_lag_1"] = source.shift(1)
            for window in [15, 60]:
                features[f"{column}_rolling_mean_{window}"] = source.rolling(window, min_periods=window).mean()
            features[f"{column}_zscore_60"] = _rolling_zscore(source, 60)

    features["intrabar_trade_price_range"] = price_max - price_min
    features["intrabar_vwap_to_close"] = _safe_div(features["agg_trade_vwap"], features["close"]) - 1.0
    features["intrabar_last_to_first_return"] = _safe_div(last_price, first_price) - 1.0
    features["intrabar_price_std_to_range"] = _safe_div(features["agg_trade_price_std"], features["intrabar_trade_price_range"])
    features["trade_flow_pressure"] = features["taker_imbalance_quantity"] * features["agg_quantity_vs_ohlcv_volume_ratio"]
    features["trade_flow_pressure_zscore_60"] = _rolling_zscore(features["trade_flow_pressure"], 60)
    event_ts = pd.to_datetime(features["event_ts"], utc=True)
    features["hour_utc"] = event_ts.dt.hour.astype("int64")
    features["day_of_week_utc"] = event_ts.dt.dayofweek.astype("int64")
    features["is_weekend_utc"] = event_ts.dt.dayofweek.isin([5, 6])
    return features


def _warmup_mask(features: pd.DataFrame) -> pd.Series:
    critical = [
        "agg_trade_count_lag_1",
        "agg_trade_count_rolling_mean_60",
        "agg_trade_count_zscore_60",
        "agg_quantity_rolling_mean_60",
        "agg_quantity_zscore_60",
        "taker_buy_ratio_quantity_lag_1",
        "taker_buy_ratio_quantity_rolling_mean_60",
        "taker_buy_ratio_quantity_zscore_60",
        "taker_imbalance_quantity_lag_1",
        "taker_imbalance_quantity_rolling_mean_60",
        "taker_imbalance_quantity_zscore_60",
        "trade_flow_pressure_zscore_60",
    ]
    mask = features[critical].isna().any(axis=1)
    if len(mask) >= 60:
        mask.iloc[:60] = True
    return mask


def _row_error_count(features: pd.DataFrame) -> pd.Series:
    invalid = pd.Series(0, index=features.index, dtype="int64")
    invalid += (features["agg_trade_count"] < 0).astype("int64")
    invalid += (features["volume"] < 0).astype("int64")
    invalid += (features["quote_volume"] < 0).astype("int64")
    invalid += (pd.to_datetime(features["feature_available_ts"], utc=True) < pd.to_datetime(features["available_ts"], utc=True)).astype("int64")
    invalid += (pd.to_datetime(features["decision_ts"], utc=True) < pd.to_datetime(features["feature_available_ts"], utc=True)).astype("int64")
    return invalid


def _validate_input_manifests(v5_manifest: dict[str, Any], trades_manifest: dict[str, Any]) -> None:
    discovery = trades_manifest["discovery"]
    if discovery["window_start"] != WINDOW_START_V7_2 or discovery["window_end"] != WINDOW_END_V7_2:
        raise ValueError("V7.2 window must exactly match V7.1.")
    if discovery["total_days"] != TOTAL_DAYS_V7_2:
        raise ValueError("V7.2 total_days must exactly match V7.1 total_days.")
    if trades_manifest["source"]["trade_source_type"] != "aggTrades":
        raise ValueError("V7.2 only accepts V7.1 aggTrades inputs.")
    if trades_manifest["source"]["market_type"] != "spot" or trades_manifest["source"]["symbol"] != "BTCUSDT":
        raise ValueError("V7.2 only accepts BTCUSDT spot trades.")
    v5_window_start = v5_manifest["discovery"]["window_start"]
    v5_window_end = v5_manifest["discovery"]["window_end"]
    if WINDOW_START_V7_2 < v5_window_start or WINDOW_END_V7_2 > v5_window_end:
        raise ValueError("V7.2 window must remain inside V5.0 OHLCV window.")


def _write_current_reports(root: Path, manifest: dict[str, Any]) -> None:
    latest_metrics = {
        "last_validated_version": "V7.1",
        "candidate_version": "V7.2",
        "candidate_status": "pending_external_audit",
        "direction": "OHLCV + public trades feature store preview",
        "window_start": manifest["window"]["window_start"],
        "window_end": manifest["window"]["window_end"],
        "total_days": manifest["window"]["total_days"],
        "trade_source_type": manifest["input_trades_manifest"]["trade_source_type"],
        "feature_columns_count": len(manifest["feature_columns"]),
        "output_rows": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"].items()},
        "labels_v7_2_created": False,
        "dataset_ml_v7_2_created": False,
        "ml_v7_2_created": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "execution_enabled": False,
        "external_validation_required": True,
    }
    _write_json(root / "reports/current/latest_metrics.json", latest_metrics)
    _write_text(
        root / "reports/current/latest_metrics.md",
        "\n".join(
            [
                "# Latest Metrics V7.2",
                "",
                "- Derniere version validee : V7.1.",
                "- Candidate : V7.2.",
                "- Direction : OHLCV + public trades feature store preview.",
                f"- Fenetre : `{manifest['window']['window_start']}` -> `{manifest['window']['window_end']}`.",
                f"- Total jours : `{manifest['window']['total_days']}`.",
                f"- Colonnes features : `{len(manifest['feature_columns'])}`.",
                f"- Rows 1m/5m/15m/1h : `{manifest['outputs']['1m']['rows']}` / `{manifest['outputs']['5m']['rows']}` / `{manifest['outputs']['15m']['rows']}` / `{manifest['outputs']['1h']['rows']}`.",
                "- Aucun label, dataset ML, modele ML, backtest, strategie, signal, ordre ou trading.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "reports/current/latest_summary.md",
        "\n".join(
            [
                "# Latest Summary V7.2",
                "",
                "V7.1 est la derniere version validee par audit externe.",
                "",
                "V7.2 est la candidate courante. Elle produit uniquement des features causales OHLCV + aggTrades sur la fenetre V7.1 de 30 jours.",
                "",
                f"Fenetre : `{manifest['window']['window_start']}` -> `{manifest['window']['window_end']}`, `{manifest['window']['total_days']}` jours.",
                f"Source trades : `{manifest['input_trades_manifest']['trade_source_type']}`.",
                f"Colonnes features : `{len(manifest['feature_columns'])}`.",
                "",
                "Aucun label V7.2, aucun dataset ML V7.2, aucun modele ML V7.2, aucun backtest, aucune strategie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading reel.",
                "",
                "V7.2 reste `pending_external_audit`.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "reports/PROJECT_STATE.md",
        "\n".join(
            [
                "# Etat du Projet : V7.1 validee + candidat V7.2",
                "",
                "- **Derniere version validee** : V7.1.",
                "- **Version candidate** : V7.2.",
                "- **Statut candidate** : `pending_external_audit`.",
                "- **Direction** : OHLCV + public trades feature store preview.",
                "",
                "## V7.2",
                "",
                f"- Fenetre : `{manifest['window']['window_start']}` -> `{manifest['window']['window_end']}`.",
                f"- Total jours : `{manifest['window']['total_days']}`.",
                f"- Source trades : `{manifest['input_trades_manifest']['trade_source_type']}`.",
                f"- Colonnes features : `{len(manifest['feature_columns'])}`.",
                "- Aucun label V7.2.",
                "- Aucun dataset ML V7.2.",
                "- Aucun modele ML V7.2.",
                "- Aucun backtest, aucune strategie, aucun signal, aucun ordre, aucun trading reel.",
                "",
                "V7.2 reste non validee avant audit externe.",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "README.md",
        "\n".join(
            [
                "# Projet Galapagos",
                "",
                "- Derniere version validee : V7.1.",
                "- Candidate : V7.2, OHLCV + public trades feature store preview.",
                "",
                "V7.2 produit uniquement des features causales OHLCV + aggTrades Binance publiques sur la fenetre V7.1 de 30 jours.",
                "",
                "Aucun label V7.2, aucun dataset ML V7.2, aucun modele ML V7.2, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre et aucun trading reel.",
                "",
                "## Commandes V7.2",
                "",
                "```bash",
                "python scripts/run_ohlcv_trades_feature_store_v7_2.py",
                "python scripts/validate_ohlcv_trades_feature_store_v7_2.py",
                "python -m pytest -q tests/features/test_ohlcv_trades_features_v7_2.py",
                "python -m pytest -q tests/validation/test_ohlcv_trades_feature_store_v7_2_validator.py",
                "python scripts/release_audit_lite_zip_v7_2.py",
                "python scripts/audit_audit_lite_zip_v7_2.py --zip projet-galapagos-v7.2-audit-lite.zip",
                "python scripts/smoke_audit_lite_zip_v7_2.py --zip projet-galapagos-v7.2-audit-lite.zip",
                "python -m pytest --collect-only -q",
                "```",
                "",
                "V7.2 reste `pending_external_audit` avant validation externe.",
            ]
        )
        + "\n",
    )


def _safe_div(numerator: Any, denominator: Any) -> pd.Series:
    numerator_series = pd.Series(numerator, dtype="float64")
    denominator_series = pd.Series(denominator, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        result = numerator_series / denominator_series
    return result.replace([np.inf, -np.inf], np.nan)


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    values = pd.Series(series, dtype="float64")
    mean = values.rolling(window, min_periods=window).mean()
    std = values.rolling(window, min_periods=window).std()
    return _safe_div(values - mean, std)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
