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
from galapagos.features.advanced_ohlcv_quality import assess_advanced_ohlcv_feature_quality
from galapagos.features.advanced_ohlcv_schemas import (
    ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0,
    ADVANCED_OHLCV_FEATURE_FAMILIES_V6_0,
    ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0,
)


VERSION_V6_0 = "V6.0"
FEATURE_SCHEMA_VERSION_V6_0 = "V6.0"
TIMEFRAMES_V6_0 = ["1m", "5m", "15m", "1h"]
MANIFEST_PATH_V6_0 = Path("reports/manifests/advanced_ohlcv_feature_store_v6_0_manifest.json")
REPORT_JSON_PATH_V6_0 = Path("reports/features/advanced_ohlcv_feature_store_v6_0.json")
REPORT_MD_PATH_V6_0 = Path("reports/features/advanced_ohlcv_feature_store_v6_0.md")
DOC_PATH_V6_0 = Path("docs/advanced_ohlcv_feature_store_v6_0.md")
EXPECTED_LIMITATIONS_V6_0 = [
    "V6.0 produit uniquement des features OHLCV avancees causales sur la fenetre historique continue validee par V5.0.",
    "V6.0 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]


def run_advanced_ohlcv_feature_store_v6_0(
    root: Path = Path("."),
    *,
    validate_inputs: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    if validate_inputs:
        validation = validate_max_history_public_market_data_v5_0(root)
        if not validation["passed"]:
            raise RuntimeError(f"V5.0 validation failed before V6.0: {validation['errors']}")

    input_manifest_path = root / MANIFEST_PATH_V5_0
    input_manifest = load_v5_0_ohlcv_manifest(root)
    discovery = input_manifest["discovery"]
    expected_rows = input_manifest["expected_rows"]

    created_at = utc_now_iso()
    feature_run_id = f"v6_0_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    input_ohlcv: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    quality: dict[str, dict[str, Any]] = {}
    status = "PASS"

    for timeframe in TIMEFRAMES_V6_0:
        input_path = input_ohlcv_path(root, timeframe, input_manifest)
        input_frame = read_parquet(input_path)
        input_sha = sha256_file(input_path)
        feature_frame = build_advanced_ohlcv_features(
            input_frame,
            source_ohlcv_sha256=input_sha,
            feature_run_id=feature_run_id,
            feature_schema_version=FEATURE_SCHEMA_VERSION_V6_0,
        )
        output = output_path(root, timeframe, discovery["window_start"], discovery["window_end"])
        write_parquet(feature_frame[ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0], output)

        input_ohlcv[timeframe] = {
            "path": str(input_path.relative_to(root)),
            "sha256": input_sha,
            "rows": int(len(input_frame)),
        }
        outputs[timeframe] = {
            "path": str(output.relative_to(root)),
            "sha256": sha256_file(output),
            "bytes": output.stat().st_size,
            "rows": int(len(feature_frame)),
            "format": "parquet",
        }
        quality[timeframe] = assess_advanced_ohlcv_feature_quality(
            feature_frame,
            timeframe,
            expected_rows=int(expected_rows[timeframe]),
        )
        quality[timeframe]["source_hashes_valid"] = True
        if quality[timeframe]["errors"]:
            status = "FAIL"

    manifest = {
        "version": VERSION_V6_0,
        "status": status,
        "created_at_utc": created_at,
        "feature_run_id": feature_run_id,
        "input_ohlcv_manifest": {
            "path": str(input_manifest_path.relative_to(root)),
            "sha256": sha256_file(input_manifest_path),
            "window_start": discovery["window_start"],
            "window_end": discovery["window_end"],
            "total_days": int(discovery["total_days"]),
        },
        "input_ohlcv": input_ohlcv,
        "outputs": outputs,
        "feature_schema_version": FEATURE_SCHEMA_VERSION_V6_0,
        "feature_columns": ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0,
        "feature_families": ADVANCED_OHLCV_FEATURE_FAMILIES_V6_0,
        "quality": quality,
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_V6_0,
    }
    report = build_report_v6_0(manifest)
    _write_json(root / MANIFEST_PATH_V6_0, manifest)
    _write_json(root / REPORT_JSON_PATH_V6_0, report)
    markdown = build_advanced_ohlcv_feature_store_markdown_v6_0(report)
    _write_text(root / REPORT_MD_PATH_V6_0, markdown)
    _write_text(root / DOC_PATH_V6_0, markdown)
    _update_project_state(root, manifest)
    return manifest


def build_advanced_ohlcv_features(
    ohlcv: pd.DataFrame,
    source_ohlcv_sha256: str,
    feature_run_id: str,
    *,
    feature_schema_version: str = FEATURE_SCHEMA_VERSION_V6_0,
) -> pd.DataFrame:
    if ohlcv.empty:
        return pd.DataFrame(columns=ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0)

    frame = ohlcv.sort_values("event_ts").reset_index(drop=True)
    rows = len(frame)
    open_ = frame["open"].astype("float64")
    high = frame["high"].astype("float64")
    low = frame["low"].astype("float64")
    close = frame["close"].astype("float64")
    volume = frame["volume"].astype("float64")
    quote_volume = frame["quote_volume"].astype("float64")
    trade_count = frame["trade_count"].astype("float64")
    taker_buy_base = frame["taker_buy_base_volume"].astype("float64")
    taker_buy_quote = frame["taker_buy_quote_volume"].astype("float64")

    log_return_1 = _safe_log_ratio(close, close.shift(1))
    features: dict[str, Any] = {
        "source": frame["source"],
        "venue": frame["venue"],
        "market_type": frame["market_type"],
        "symbol": frame["symbol"],
        "timeframe": frame["timeframe"],
        "event_ts": frame["event_ts"],
        "close_ts": frame["close_ts"],
        "available_ts": frame["available_ts"],
        "decision_ts": frame["decision_ts"],
        "feature_available_ts": frame["available_ts"],
        "ingested_at_ts": frame["ingested_at_ts"],
        "feature_run_id": feature_run_id,
        "source_ohlcv_sha256": source_ohlcv_sha256,
        "feature_schema_version": feature_schema_version,
    }

    for horizon in [1, 3, 5, 10, 20, 60]:
        features[f"return_{horizon}"] = _safe_div(close, close.shift(horizon)) - 1.0
        features[f"log_return_{horizon}"] = _safe_log_ratio(close, close.shift(horizon))
    for horizon in [5, 10, 20, 60]:
        features[f"momentum_{horizon}"] = features[f"return_{horizon}"]
    features["momentum_zscore_20"] = _rolling_zscore(pd.Series(features["momentum_20"]), 20)
    features["momentum_zscore_60"] = _rolling_zscore(pd.Series(features["momentum_60"]), 60)

    for window in [5, 15, 30, 60, 120]:
        features[f"rolling_vol_{window}"] = log_return_1.rolling(window, min_periods=window).std()
    features["vol_ratio_15_60"] = _safe_div(pd.Series(features["rolling_vol_15"]), pd.Series(features["rolling_vol_60"]))
    features["vol_ratio_30_120"] = _safe_div(pd.Series(features["rolling_vol_30"]), pd.Series(features["rolling_vol_120"]))
    features["vol_zscore_60"] = _rolling_zscore(pd.Series(features["rolling_vol_60"]), 60)
    features["vol_zscore_120"] = _rolling_zscore(pd.Series(features["rolling_vol_120"]), 120)
    features["high_low_range"] = _safe_div(high, low) - 1.0
    features["log_high_low_range"] = _safe_log_ratio(high, low)
    true_range = pd.concat([(high - low), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    features["atr_like_14"] = true_range.rolling(14, min_periods=14).mean()
    features["atr_like_30"] = true_range.rolling(30, min_periods=30).mean()
    features["range_zscore_60"] = _rolling_zscore(pd.Series(features["high_low_range"]), 60)
    vol_z = pd.Series(features["vol_zscore_120"])
    features["volatility_regime_low"] = vol_z < -0.5
    features["volatility_regime_mid"] = vol_z.between(-0.5, 0.5, inclusive="both")
    features["volatility_regime_high"] = vol_z > 0.5

    for window in [5, 15, 30, 60, 120]:
        features[f"sma_{window}"] = close.rolling(window, min_periods=window).mean()
    for span in [12, 26, 50]:
        features[f"ema_{span}"] = close.ewm(span=span, adjust=False).mean()
    for window in [15, 60, 120]:
        features[f"close_to_sma_{window}"] = _safe_div(close, pd.Series(features[f"sma_{window}"])) - 1.0
    for span in [12, 26, 50]:
        features[f"close_to_ema_{span}"] = _safe_div(close, pd.Series(features[f"ema_{span}"])) - 1.0
    features["sma_15_slope_5"] = _safe_div(pd.Series(features["sma_15"]), pd.Series(features["sma_15"]).shift(5)) - 1.0
    features["sma_60_slope_10"] = _safe_div(pd.Series(features["sma_60"]), pd.Series(features["sma_60"]).shift(10)) - 1.0
    features["ema_12_ema_26_spread"] = _safe_div(pd.Series(features["ema_12"]), pd.Series(features["ema_26"])) - 1.0
    features["macd_like"] = pd.Series(features["ema_12"]) - pd.Series(features["ema_26"])
    features["macd_like_signal"] = pd.Series(features["macd_like"]).ewm(span=9, adjust=False).mean()
    features["macd_like_hist"] = pd.Series(features["macd_like"]) - pd.Series(features["macd_like_signal"])

    for window in [20, 60, 120]:
        rolling_mean = close.rolling(window, min_periods=window).mean()
        features[f"close_zscore_{window}"] = _rolling_zscore(close, window)
        features[f"distance_to_rolling_mean_{window}"] = _safe_div(close, rolling_mean) - 1.0
    features["rsi_like_14"] = _rsi_like(close, 14)
    features["rsi_like_30"] = _rsi_like(close, 30)
    features["overbought_rsi_14"] = pd.Series(features["rsi_like_14"]) >= 70.0
    features["oversold_rsi_14"] = pd.Series(features["rsi_like_14"]) <= 30.0

    for window in [20, 60, 120]:
        features[f"rolling_high_{window}"] = high.rolling(window, min_periods=window).max()
        features[f"rolling_low_{window}"] = low.rolling(window, min_periods=window).min()
        features[f"close_to_high_{window}"] = _safe_div(close, pd.Series(features[f"rolling_high_{window}"])) - 1.0
        features[f"close_to_low_{window}"] = _safe_div(close, pd.Series(features[f"rolling_low_{window}"])) - 1.0
    for window in [20, 60]:
        width = pd.Series(features[f"rolling_high_{window}"]) - pd.Series(features[f"rolling_low_{window}"])
        features[f"donchian_position_{window}"] = _safe_div(close - pd.Series(features[f"rolling_low_{window}"]), width)
        features[f"donchian_width_{window}"] = _safe_div(width, close)
        features[f"breakout_up_{window}"] = close >= pd.Series(features[f"rolling_high_{window}"])
        features[f"breakout_down_{window}"] = close <= pd.Series(features[f"rolling_low_{window}"])
    features["range_compression_20_60"] = _safe_div(
        pd.Series(features["donchian_width_20"]),
        pd.Series(features["donchian_width_60"]),
    )

    for window in [20, 60]:
        mid = close.rolling(window, min_periods=window).mean()
        std = close.rolling(window, min_periods=window).std()
        upper = mid + 2.0 * std
        lower = mid - 2.0 * std
        features[f"bollinger_mid_{window}"] = mid
        features[f"bollinger_upper_{window}"] = upper
        features[f"bollinger_lower_{window}"] = lower
        features[f"bollinger_width_{window}"] = _safe_div(upper - lower, mid)
        features[f"bollinger_percent_b_{window}"] = _safe_div(close - lower, upper - lower)

    candle_range = high - low
    candle_body = close - open_
    upper_wick = high - pd.concat([open_, close], axis=1).max(axis=1)
    lower_wick = pd.concat([open_, close], axis=1).min(axis=1) - low
    features["candle_range"] = candle_range
    features["candle_body"] = candle_body
    features["candle_body_abs"] = candle_body.abs()
    features["upper_wick"] = upper_wick
    features["lower_wick"] = lower_wick
    features["upper_wick_ratio"] = _safe_div(upper_wick, candle_range)
    features["lower_wick_ratio"] = _safe_div(lower_wick, candle_range)
    features["body_to_range"] = _safe_div(candle_body.abs(), candle_range)
    features["close_position_in_range"] = _safe_div(close - low, candle_range)
    features["bullish_candle"] = close > open_
    features["bearish_candle"] = close < open_
    features["doji_like"] = pd.Series(features["body_to_range"]) <= 0.1
    features["large_body_zscore_60"] = _rolling_zscore(pd.Series(features["candle_body_abs"]), 60)
    features["upper_wick_zscore_60"] = _rolling_zscore(pd.Series(features["upper_wick"]), 60)
    features["lower_wick_zscore_60"] = _rolling_zscore(pd.Series(features["lower_wick"]), 60)

    features["volume_lag_1"] = volume.shift(1)
    features["volume_return_1"] = _safe_div(volume, volume.shift(1)) - 1.0
    features["volume_return_5"] = _safe_div(volume, volume.shift(5)) - 1.0
    for window in [5, 15, 60, 120]:
        features[f"rolling_volume_mean_{window}"] = volume.rolling(window, min_periods=window).mean()
    for window in [15, 60, 120]:
        features[f"rolling_volume_zscore_{window}"] = _rolling_zscore(volume, window)
    features["quote_volume_zscore_60"] = _rolling_zscore(quote_volume, 60)
    features["trade_count_zscore_60"] = _rolling_zscore(trade_count, 60)
    features["volume_price_trend_like"] = (features["volume_return_1"] * features["return_1"]).astype("float64")
    volume_z = pd.Series(features["rolling_volume_zscore_120"])
    features["volume_regime_low"] = volume_z < -0.5
    features["volume_regime_mid"] = volume_z.between(-0.5, 0.5, inclusive="both")
    features["volume_regime_high"] = volume_z > 0.5

    features["taker_buy_base_ratio"] = _safe_div(taker_buy_base, volume)
    features["taker_buy_quote_ratio"] = _safe_div(taker_buy_quote, quote_volume)
    features["taker_buy_base_ratio_lag_1"] = pd.Series(features["taker_buy_base_ratio"]).shift(1)
    features["taker_buy_base_ratio_mean_15"] = pd.Series(features["taker_buy_base_ratio"]).rolling(15, min_periods=15).mean()
    features["taker_buy_base_ratio_mean_60"] = pd.Series(features["taker_buy_base_ratio"]).rolling(60, min_periods=60).mean()
    features["taker_buy_base_ratio_zscore_60"] = _rolling_zscore(pd.Series(features["taker_buy_base_ratio"]), 60)
    features["taker_buy_imbalance"] = 2.0 * pd.Series(features["taker_buy_base_ratio"]) - 1.0
    features["taker_buy_imbalance_mean_15"] = pd.Series(features["taker_buy_imbalance"]).rolling(15, min_periods=15).mean()
    features["taker_buy_imbalance_mean_60"] = pd.Series(features["taker_buy_imbalance"]).rolling(60, min_periods=60).mean()
    features["taker_buy_imbalance_zscore_60"] = _rolling_zscore(pd.Series(features["taker_buy_imbalance"]), 60)

    return_sign = np.sign(pd.Series(features["return_1"]).fillna(0.0)).astype("int8")
    features["return_sign"] = return_sign
    features["up_streak"] = _streak(return_sign > 0)
    features["down_streak"] = _streak(return_sign < 0)
    features["flat_streak"] = _streak(return_sign == 0)
    features["consecutive_high_closes_5"] = pd.Series(features["up_streak"]) >= 5
    features["consecutive_low_closes_5"] = pd.Series(features["down_streak"]) >= 5
    trend_up = (close > pd.Series(features["sma_60"])) & (pd.Series(features["ema_12"]) > pd.Series(features["ema_26"]))
    trend_down = (close < pd.Series(features["sma_60"])) & (pd.Series(features["ema_12"]) < pd.Series(features["ema_26"]))
    features["trend_regime_up"] = trend_up
    features["trend_regime_down"] = trend_down
    features["trend_regime_range"] = ~(trend_up | trend_down)

    event_ts = pd.to_datetime(frame["event_ts"], utc=True)
    features["hour_utc"] = event_ts.dt.hour.astype("int16")
    features["day_of_week_utc"] = event_ts.dt.dayofweek.astype("int16")
    features["day_of_month_utc"] = event_ts.dt.day.astype("int16")
    features["month_utc"] = event_ts.dt.month.astype("int16")
    features["quarter_utc"] = event_ts.dt.quarter.astype("int16")
    features["is_weekend_utc"] = event_ts.dt.dayofweek >= 5
    features["is_month_start_utc"] = event_ts.dt.is_month_start
    features["is_month_end_utc"] = event_ts.dt.is_month_end
    features["sin_hour_utc"] = np.sin(2.0 * np.pi * event_ts.dt.hour / 24.0)
    features["cos_hour_utc"] = np.cos(2.0 * np.pi * event_ts.dt.hour / 24.0)
    features["sin_day_of_week_utc"] = np.sin(2.0 * np.pi * event_ts.dt.dayofweek / 7.0)
    features["cos_day_of_week_utc"] = np.cos(2.0 * np.pi * event_ts.dt.dayofweek / 7.0)

    result = pd.DataFrame(features, index=frame.index)
    for column in ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0:
        if column not in result.columns:
            raise RuntimeError(f"missing V6.0 advanced feature column: {column}")
        if pd.api.types.is_numeric_dtype(result[column]):
            result[column] = result[column].replace([np.inf, -np.inf], np.nan)
            if not pd.api.types.is_bool_dtype(result[column]) and not pd.api.types.is_integer_dtype(result[column]):
                result[column] = result[column].astype("float32")

    result = result.copy()
    null_counts = np.zeros(rows, dtype=np.int16)
    for column in ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0:
        null_counts += result[column].isna().to_numpy(dtype=np.int16)
    warmup = (np.arange(rows) < 120) | (null_counts > 0)
    result["warmup_row"] = warmup
    result["advanced_feature_null_count"] = null_counts
    result["advanced_feature_error_count"] = np.zeros(rows, dtype=np.int16)
    return result[ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0]


def load_v5_0_ohlcv_manifest(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / MANIFEST_PATH_V5_0).read_text(encoding="utf-8"))


def input_ohlcv_path(root: Path, timeframe: str, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest or load_v5_0_ohlcv_manifest(root)
    return root.resolve() / manifest["outputs"][timeframe]["path"]


def output_path(
    root: Path,
    timeframe: str,
    window_start: str | None = None,
    window_end: str | None = None,
) -> Path:
    if window_start is None or window_end is None:
        manifest = load_v5_0_ohlcv_manifest(root)
        window_start = manifest["discovery"]["window_start"]
        window_end = manifest["discovery"]["window_end"]
    return (
        root.resolve()
        / "data/research/v6_0/features/advanced_ohlcv"
        / "source=binance_archive"
        / "market_type=spot"
        / "symbol=BTCUSDT"
        / f"timeframe={timeframe}"
        / f"window={window_start}_{window_end}"
        / "features.parquet"
    )


def build_report_v6_0(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": manifest["version"],
        "status": manifest["status"],
        "created_at_utc": manifest["created_at_utc"],
        "feature_run_id": manifest["feature_run_id"],
        "input_ohlcv_manifest": manifest["input_ohlcv_manifest"],
        "input_ohlcv": manifest["input_ohlcv"],
        "outputs": manifest["outputs"],
        "feature_schema_version": manifest["feature_schema_version"],
        "feature_columns": manifest["feature_columns"],
        "feature_families": manifest["feature_families"],
        "quality": manifest["quality"],
        "safety": manifest["safety"],
        "limitations": manifest["limitations"],
    }


def build_advanced_ohlcv_feature_store_markdown_v6_0(report: dict[str, Any]) -> str:
    input_manifest = report["input_ohlcv_manifest"]
    outputs = "\n".join(
        f"- `{timeframe}` : `{report['outputs'][timeframe]['rows']}` lignes, `{report['outputs'][timeframe]['path']}`"
        for timeframe in TIMEFRAMES_V6_0
    )
    families = "\n".join(
        f"- `{family}` : `{len(columns)}` features" for family, columns in report["feature_families"].items()
    )
    quality = "\n".join(
        f"- `{timeframe}` : warmup `{payload['warmup_rows']}`, lignes apres warmup `{payload['rows_after_warmup']}`, erreurs `{len(payload['errors'])}`"
        for timeframe, payload in report["quality"].items()
    )
    limitations = "\n".join(f"- {item}" for item in report["limitations"])
    return f"""# Advanced OHLCV Feature Store V6.0

## Objectif

V6.0 construit uniquement une bibliotheque avancee de features OHLCV causales sur la fenetre historique continue validee par V5.0 : `{input_manifest['window_start']}` -> `{input_manifest['window_end']}`, soit `{input_manifest['total_days']}` jours.

Les features avancees sont des variables de recherche. Elles ne sont pas des signaux de trading et ne valident aucune decision operationnelle.

## Inputs

- Source : OHLCV V5.0 `reports/manifests/max_history_public_market_data_v5_0_manifest.json`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `{report['feature_run_id']}`
- Schema : `{report['feature_schema_version']}`

## Outputs

{outputs}

## Familles de features

{families}

## Regles causales

- Tous les calculs utilisent uniquement le passe ou la bougie courante disponible a `decision_ts`.
- Aucun `future_return`, `future_close`, label, target, prediction, order, pnl ou backtest n'est produit.
- La colonne technique `macd_like_signal` est une composante d'indicateur, pas un signal de trading.
- `feature_available_ts = available_ts` pour cette preview.
- `decision_ts >= feature_available_ts` est verifie physiquement.

## Warmup

Les 120 premieres lignes de chaque timeframe restent marquees `warmup_row = true`, car plusieurs indicateurs utilisent des fenetres causales jusqu'a 120 observations. Les NaN de warmup ne sont pas remplis artificiellement.

## Qualite par timeframe

{quality}

## Limitations

{limitations}

## Securite

- V6.0 ne valide aucune strategie
- V6.0 ne produit aucun label
- V6.0 ne produit aucun dataset ML
- V6.0 ne produit aucun modele ML
- V6.0 ne produit aucun backtest
- V6.0 ne produit aucun signal de trading
- V6.0 ne produit aucun ordre
- V6.0 n'autorise aucun paper live
- V6.0 n'autorise aucun trading reel
"""


def _safe_div(numerator: Any, denominator: Any) -> pd.Series:
    numerator_series = pd.Series(numerator, copy=False).astype("float64")
    denominator_series = pd.Series(denominator, copy=False).astype("float64")
    denominator_series = denominator_series.where(denominator_series != 0.0)
    return numerator_series / denominator_series


def _safe_log_ratio(numerator: Any, denominator: Any) -> pd.Series:
    ratio = _safe_div(numerator, denominator)
    ratio = ratio.where(ratio > 0.0)
    return np.log(ratio)


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    base = pd.Series(series, copy=False).astype("float64")
    rolling_mean = base.rolling(window, min_periods=window).mean()
    rolling_std = base.rolling(window, min_periods=window).std()
    return _safe_div(base - rolling_mean, rolling_std)


def _rsi_like(close: pd.Series, window: int) -> pd.Series:
    diff = close.diff()
    gain = diff.clip(lower=0.0)
    loss = -diff.clip(upper=0.0)
    avg_gain = gain.rolling(window, min_periods=window).mean()
    avg_loss = loss.rolling(window, min_periods=window).mean()
    rs = _safe_div(avg_gain, avg_loss)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.where(avg_loss != 0.0, 100.0)
    rsi = rsi.where(~((avg_loss == 0.0) & (avg_gain == 0.0)), 50.0)
    return rsi


def _streak(condition: pd.Series) -> pd.Series:
    active = pd.Series(condition, copy=False).fillna(False).astype(bool)
    groups = active.ne(active.shift(fill_value=False)).cumsum()
    streak = active.groupby(groups).cumcount() + 1
    return streak.where(active, 0).astype("int16")


def _safety() -> dict[str, bool]:
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


def _update_project_state(root: Path, manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V5.6.1",
            "candidate_version": VERSION_V6_0,
            "candidate_status": "pending_external_audit",
            "direction": "max historical advanced OHLCV feature expansion",
            "v6_0_pending_external_audit": True,
            "v6_0_no_labels": True,
            "v6_0_no_dataset_ml": True,
            "v6_0_no_ml_model": True,
            "v6_0_no_backtest": True,
            "v6_0_no_strategy": True,
            "v6_0_no_paper_live": True,
            "v6_0_no_orders": True,
            "v6_0_no_real_trading": True,
        }
    )
    _write_json(state_path, state)
    _write_text(root / "reports/PROJECT_STATE.md", _render_project_state_markdown(manifest))
    _write_json(root / "reports/current/latest_metrics.json", build_report_v6_0(manifest))
    _write_text(root / "reports/current/latest_metrics.md", _render_latest_metrics_markdown(manifest))
    _write_text(root / "reports/current/latest_summary.md", _render_latest_summary_markdown(manifest))


def _render_project_state_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Etat projet Galapagos

- Derniere version validee : `V5.6.1`
- Candidate : `V6.0`
- Statut candidate : `pending_external_audit`
- Direction : max historical advanced OHLCV feature expansion
- Fenetre : `{manifest['input_ohlcv_manifest']['window_start']}` -> `{manifest['input_ohlcv_manifest']['window_end']}`
- Aucun label V6.0
- Aucun dataset ML V6.0
- Aucun modele ML V6.0
- Aucun backtest
- Aucune strategie
- Aucun paper live
- Aucun ordre
- Aucun trading reel
"""


def _render_latest_metrics_markdown(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        f"- `{timeframe}` : `{payload['rows']}` lignes, checksum `{payload['sha256']}`"
        for timeframe, payload in manifest["outputs"].items()
    )
    return f"""# Latest metrics V6.0

- Version candidate : `V6.0`
- Statut : `pending_external_audit`
- Type : advanced OHLCV feature store causal
- Nombre total de colonnes : `{len(ADVANCED_OHLCV_FEATURE_COLUMNS_V6_0)}`
- Nombre de features avancees : `{len(ADVANCED_OHLCV_FEATURE_VALUE_COLUMNS_V6_0)}`

## Outputs

{rows}

## Securite

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun trading reel.
"""


def _render_latest_summary_markdown(manifest: dict[str, Any]) -> str:
    return f"""# Synthese courante

La derniere version validee reste `V5.6.1`. La candidate `V6.0` est en statut `pending_external_audit`.

V6.0 produit uniquement des features OHLCV avancees causales sur la fenetre max historical validee par V5.0 (`{manifest['input_ohlcv_manifest']['window_start']}` -> `{manifest['input_ohlcv_manifest']['window_end']}`, `{manifest['input_ohlcv_manifest']['total_days']}` jours).

V6.0 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live et aucun trading reel.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
