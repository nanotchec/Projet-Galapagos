from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

EXPECTED_METRICS = [
    ("binance", "funding_rate"),
    ("bybit", "funding_rate"),
    ("binance", "open_interest"),
    ("bybit", "open_interest"),
    ("binance", "premium"),
    ("bybit", "premium"),
    ("binance", "taker_buy_sell_ratio"),
    ("bybit", "taker_buy_sell_ratio"),
    ("binance", "long_short_ratio"),
    ("bybit", "long_short_ratio"),
    ("coinglass", "liquidations"),
    ("coinglass", "aggregated_open_interest"),
    ("coinglass", "btc_etf_flows"),
    ("coinglass", "perp_basis_multi_exchange"),
]

METRIC_METADATA = {
    ("binance", "funding_rate"): {
        "endpoint_name": "fapi/v1/fundingRate",
        "granularity": "8h",
        "history_limit": "public paginated, implementation currently bounded by request limit",
        "rate_limit_note": "public rate limits apply",
        "alignment_risk": "low",
        "priority_for_signal_quality": "high",
        "provider_gap": "none",
        "rows_expected_estimate": 1095,
    },
    ("bybit", "funding_rate"): {
        "endpoint_name": "v5/market/funding/history",
        "granularity": "8h",
        "history_limit": "public endpoint bounded by pagination limit in this collector",
        "rate_limit_note": "public rate limits apply",
        "alignment_risk": "low",
        "priority_for_signal_quality": "high",
        "provider_gap": "public_history_limited",
        "rows_expected_estimate": 1095,
    },
    ("binance", "open_interest"): {
        "endpoint_name": "futures/data/openInterestHist",
        "granularity": "5m-1d depending period",
        "history_limit": "endpoint may reject or limit history depending symbol/period",
        "rate_limit_note": "public data endpoint limits apply",
        "alignment_risk": "medium",
        "priority_for_signal_quality": "high",
        "provider_gap": "public_history_limited",
        "rows_expected_estimate": 4380,
    },
    ("bybit", "open_interest"): {
        "endpoint_name": "v5/market/open-interest",
        "granularity": "4h requested",
        "history_limit": "limit=200 per request in current collector",
        "rate_limit_note": "public rate limits apply",
        "alignment_risk": "medium",
        "priority_for_signal_quality": "high",
        "provider_gap": "public_history_limited",
        "rows_expected_estimate": 4380,
    },
    ("binance", "premium"): {
        "endpoint_name": "fapi/v1/premiumIndex",
        "granularity": "snapshot in current collector",
        "history_limit": "historical premium not fully integrated",
        "rate_limit_note": "public rate limits apply",
        "alignment_risk": "medium",
        "priority_for_signal_quality": "medium",
        "provider_gap": "public_history_limited",
        "rows_expected_estimate": 4380,
    },
    ("bybit", "premium"): {
        "endpoint_name": "v5/market/tickers",
        "granularity": "snapshot in current collector",
        "history_limit": "historical premium not fully integrated",
        "rate_limit_note": "public rate limits apply",
        "alignment_risk": "medium",
        "priority_for_signal_quality": "medium",
        "provider_gap": "public_history_limited",
        "rows_expected_estimate": 4380,
    },
    ("binance", "taker_buy_sell_ratio"): {
        "endpoint_name": "futures/data/takerlongshortRatio",
        "granularity": "4h requested",
        "history_limit": "limited public lookback",
        "rate_limit_note": "public data endpoint limits apply",
        "alignment_risk": "medium",
        "priority_for_signal_quality": "medium",
        "provider_gap": "public_history_limited",
        "rows_expected_estimate": 4380,
    },
    ("binance", "long_short_ratio"): {
        "endpoint_name": "futures/data/globalLongShortAccountRatio",
        "granularity": "4h requested",
        "history_limit": "limited public lookback",
        "rate_limit_note": "public data endpoint limits apply",
        "alignment_risk": "medium",
        "priority_for_signal_quality": "medium",
        "provider_gap": "public_history_limited",
        "rows_expected_estimate": 4380,
    },
}


def audit_derivatives_coverage(
    symbol: str,
    timeframe: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    ohlcv = _load_ohlcv(symbol, timeframe)
    ohlcv_rows = len(ohlcv)
    start = str(ohlcv["timestamp"].min()) if not ohlcv.empty else None
    end = str(ohlcv["timestamp"].max()) if not ohlcv.empty else None
    records = _load_derivatives(symbol)
    feature_columns = _load_feature_columns(symbol, timeframe)
    checks = []
    for source, metric in EXPECTED_METRICS:
        subset = records[
            (records.get("source") == source) & (records.get("metric_name") == metric)
        ] if not records.empty else pd.DataFrame()
        status = _metric_status(source, metric, subset)
        rows = int(len(subset))
        coverage_pct = None if ohlcv_rows == 0 else min(rows / ohlcv_rows, 1.0)
        timestamps = pd.to_datetime(subset["timestamp"], utc=True, errors="coerce") if rows else []
        checks.append(
            {
                "source": source,
                "metric_name": metric,
                "status": status,
                "rows": rows,
                "start_timestamp": str(timestamps.min()) if rows else None,
                "end_timestamp": str(timestamps.max()) if rows else None,
                "coverage_pct_vs_ohlcv": coverage_pct,
                "missing_rate": None if coverage_pct is None else 1.0 - coverage_pct,
                "freshness": _freshness(timestamps) if rows else "unknown",
                "known_limitations": _known_limitations(source, metric, status),
                "included_in_dataset": _included(metric, feature_columns),
            }
        )
    verdict = _coverage_verdict(checks)
    return {
        "version": "V1.14",
        "symbol": symbol,
        "timeframe": timeframe,
        "dry_run": dry_run,
        "ohlcv_rows": ohlcv_rows,
        "ohlcv_start": start,
        "ohlcv_end": end,
        "checks": checks,
        "verdict": verdict,
        "codex_cli_called": False,
        "holdout_executed": False,
    }


def audit_derivatives_coverage_expansion(
    symbol: str,
    timeframe: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    base = audit_derivatives_coverage(symbol, timeframe, dry_run=dry_run)
    expanded = []
    for item in base["checks"]:
        key = (item["source"], item["metric_name"])
        metadata = _metric_metadata(*key)
        rows_local = item["rows"]
        rows_expected = metadata["rows_expected_estimate"]
        status = item["status"]
        provider_gap = metadata["provider_gap"]
        if status in {"requires_api_key"}:
            provider_gap = "requires_paid_provider"
        elif status in {"not_supported"}:
            provider_gap = "endpoint_not_supported"
        elif status in {"history_limited"}:
            provider_gap = "public_history_limited"
        expanded.append(
            {
                **item,
                "endpoint_name": metadata["endpoint_name"],
                "rows_local": rows_local,
                "rows_expected_estimate": rows_expected,
                "granularity": metadata["granularity"],
                "history_limit": metadata["history_limit"],
                "rate_limit_note": metadata["rate_limit_note"],
                "alignment_risk": metadata["alignment_risk"],
                "priority_for_signal_quality": metadata["priority_for_signal_quality"],
                "provider_gap": provider_gap,
                "collectable_but_not_integrated": (
                    provider_gap == "public_history_limited"
                    and rows_local == 0
                    and status == "unavailable"
                ),
            }
        )
    return {
        "version": "V1.14",
        "symbol": symbol,
        "timeframe": timeframe,
        "dry_run": dry_run,
        "ohlcv_rows": base["ohlcv_rows"],
        "ohlcv_start": base["ohlcv_start"],
        "ohlcv_end": base["ohlcv_end"],
        "metrics": expanded,
        "verdicts": _expansion_verdicts(expanded),
        "codex_cli_called": False,
        "holdout_executed": False,
    }


def derivatives_data_quality(symbol: str, timeframe: str) -> dict[str, Any]:
    records = _load_derivatives(symbol)
    features = _load_features(symbol, timeframe)
    duplicate_rows = (
        int(records.duplicated(["source", "metric_name", "timestamp"]).sum())
        if not records.empty
        else 0
    )
    missing_rates = {
        column: float(features[column].isna().mean())
        for column in features.columns
        if features[column].isna().any()
    } if not features.empty else {}
    disagreements = {}
    if {"funding_rate_binance", "funding_rate_bybit"}.issubset(features.columns):
        disagreements["funding_abs_diff_mean"] = float(
            (features["funding_rate_binance"] - features["funding_rate_bybit"]).abs().mean()
        )
    verdict = "DERIVATIVES_DATA_TOO_SPARSE"
    if not features.empty and len(features) > 100:
        verdict = "DERIVATIVES_DATA_PARTIAL"
    if not missing_rates and not features.empty:
        verdict = "DERIVATIVES_DATA_USABLE"
    return {
        "version": "V1.14",
        "symbol": symbol,
        "timeframe": timeframe,
        "records_rows": int(len(records)),
        "features_rows": int(len(features)),
        "duplicate_rows": duplicate_rows,
        "missing_rates": missing_rates,
        "source_disagreements": disagreements,
        "known_limitations": [
            "Premium snapshots are sparse unless historical mark/index is available.",
            "Bybit public taker and long/short history are not fully covered here.",
            "Liquidations require a dedicated provider such as CoinGlass.",
        ],
        "features_safe_for_research": bool(not features.empty),
        "verdict": verdict,
    }


def _load_ohlcv(symbol: str, timeframe: str) -> pd.DataFrame:
    path = (
        Path("data/silver/ohlcv/binance")
        / symbol
        / timeframe
        / f"{symbol}_{timeframe}_combined.csv"
    )
    if not path.exists():
        return pd.DataFrame(columns=["timestamp"])
    data = pd.read_csv(path)
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    return data


def _load_derivatives(symbol: str) -> pd.DataFrame:
    frames = []
    base = Path("data/silver/derivatives")
    if base.exists():
        for path in sorted(base.glob(f"*/{symbol}/*.csv")):
            try:
                frames.append(pd.read_csv(path))
            except Exception:
                continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _load_features(symbol: str, timeframe: str) -> pd.DataFrame:
    path = Path("data/gold/derivatives_features") / symbol / timeframe / "derivatives_features.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _load_feature_columns(symbol: str, timeframe: str) -> set[str]:
    return set(_load_features(symbol, timeframe).columns)


def _metric_status(source: str, metric: str, subset: pd.DataFrame) -> str:
    if source == "coinglass":
        return "requires_api_key"
    if not subset.empty:
        return "history_limited" if metric == "long_short_ratio" else "available"
    if source == "bybit" and metric in {"taker_buy_sell_ratio", "long_short_ratio"}:
        return "not_supported"
    if metric in {"aggregated_open_interest", "btc_etf_flows", "perp_basis_multi_exchange"}:
        return "requires_api_key"
    if metric == "liquidations":
        return "requires_api_key"
    return "unavailable"


def _known_limitations(source: str, metric: str, status: str) -> str | None:
    if metric == "liquidations":
        return "Historical liquidations require CoinGlass or another provider."
    if status == "history_limited":
        return "Public endpoint has limited lookback."
    if status == "not_supported":
        return f"{source} public endpoint is not integrated for {metric}."
    return None


def _included(metric: str, feature_columns: set[str]) -> bool:
    aliases = {
        "funding_rate": {"funding_rate_mean", "funding_rate_binance", "funding_rate_bybit"},
        "open_interest": {"open_interest_mean", "open_interest_binance", "open_interest_bybit"},
        "premium": {"premium_mean", "premium_binance", "premium_bybit"},
        "taker_buy_sell_ratio": {"taker_buy_sell_ratio", "taker_imbalance"},
        "long_short_ratio": {"long_short_ratio", "long_short_ratio_zscore"},
    }
    return bool(aliases.get(metric, {metric}) & feature_columns)


def _freshness(timestamps: pd.Series) -> str:
    max_ts = timestamps.max()
    if pd.isna(max_ts):
        return "unknown"
    age_days = (pd.Timestamp.utcnow() - max_ts).days
    if age_days <= 2:
        return "fresh"
    if age_days <= 30:
        return "recent"
    return "stale"


def _coverage_verdict(checks: list[dict[str, Any]]) -> str:
    available = [item for item in checks if item["status"] in {"available", "history_limited"}]
    if len(available) >= 5:
        return "DERIVATIVES_DATA_PARTIAL"
    if len(available) >= 2:
        return "DERIVATIVES_DATA_TOO_SPARSE"
    return "NEED_PROVIDER_UPGRADE"


def _metric_metadata(source: str, metric: str) -> dict[str, Any]:
    default = {
        "endpoint_name": "not_available_public_or_not_integrated",
        "granularity": "unknown",
        "history_limit": "unknown",
        "rate_limit_note": "unknown",
        "alignment_risk": "high",
        "priority_for_signal_quality": "medium",
        "provider_gap": "requires_paid_provider",
        "rows_expected_estimate": 4380,
    }
    if metric == "liquidations":
        default |= {
            "endpoint_name": "paid_provider_liquidations",
            "priority_for_signal_quality": "high",
            "history_limit": "requires dedicated provider for usable history",
        }
    if source == "coinglass":
        default |= {
            "endpoint_name": f"coinglass_{metric}",
            "history_limit": "requires API key and plan check",
            "rate_limit_note": "depends on paid plan",
        }
    return METRIC_METADATA.get((source, metric), default)


def _expansion_verdicts(metrics: list[dict[str, Any]]) -> list[str]:
    verdicts: list[str] = []
    available = [item for item in metrics if item["status"] in {"available", "history_limited"}]
    paid_needed = [item for item in metrics if item["provider_gap"] == "requires_paid_provider"]
    sparse_high = [
        item for item in metrics
        if item["priority_for_signal_quality"] == "high"
        and item["status"] not in {"available", "history_limited"}
    ]
    if len(available) >= 6:
        verdicts.append("PUBLIC_DATA_PARTIAL_BUT_USABLE")
    else:
        verdicts.append("NEED_MORE_PUBLIC_COLLECTION")
    if sparse_high:
        verdicts.append("PUBLIC_DATA_TOO_SPARSE")
    if any(item["metric_name"] == "liquidations" for item in paid_needed):
        verdicts.append("PAID_PROVIDER_NEEDED_FOR_LIQUIDATIONS")
    verdicts.append("PAID_PROVIDER_NOT_JUSTIFIED_YET")
    return verdicts
