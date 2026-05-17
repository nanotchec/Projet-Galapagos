from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any

BASE_URL = "https://fapi.binance.com"


def build_binance_futures_plan(symbol: str, days: int) -> dict:
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    endpoints = {
        "funding_rate": "/fapi/v1/fundingRate",
        "open_interest": "/fapi/v1/openInterest",
        "premium_index": "/fapi/v1/premiumIndex",
        "taker_buy_sell": "/futures/data/takerlongshortRatio",
        "long_short_ratio": "/futures/data/globalLongShortAccountRatio",
    }
    return {
        metric: f"{BASE_URL}{path}?{urllib.parse.urlencode({'symbol': symbol})}"
        for metric, path in endpoints.items()
    } | {
        "symbol": symbol,
        "start_timestamp": start.isoformat(),
        "end_timestamp": end.isoformat(),
        "history_limitations": {"long_short_ratio": "history_limited"},
    }


def fetch_binance_public_derivatives(symbol: str, days: int, timeout: int = 20) -> dict[str, Any]:
    """Fetch public Binance USD-M derivatives metrics with per-metric status."""
    now = datetime.now(UTC)
    start_ms = int((now - timedelta(days=days)).timestamp() * 1000)
    end_ms = int(now.timestamp() * 1000)
    metrics: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    funding_rows = _request_paginated_funding(symbol, start_ms, end_ms, timeout)
    if isinstance(funding_rows, list):
        metric_rows = [
            _record(
                timestamp=item.get("fundingTime"),
                source="binance",
                symbol=symbol,
                metric_name="funding_rate",
                metric_value=item.get("fundingRate"),
                delay_ms=0,
            )
            for item in funding_rows
        ]
        rows.extend(metric_rows)
        metrics["funding_rate"] = _status("available", metric_rows)
    else:
        metrics["funding_rate"] = _status("unavailable", [], funding_rows)

    open_interest_hist = _request_json(
        "/futures/data/openInterestHist",
        {
            "pair": symbol,
            "contractType": "PERPETUAL",
            "period": "4h",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 500,
        },
        timeout,
    )
    if isinstance(open_interest_hist, list):
        metric_rows = [
            _record(
                timestamp=item.get("timestamp"),
                source="binance",
                symbol=symbol,
                metric_name="open_interest",
                metric_value=item.get("sumOpenInterest"),
                delay_ms=0,
            )
            for item in open_interest_hist
        ]
        rows.extend(metric_rows)
        metrics["open_interest"] = _status("available", metric_rows)
    else:
        metrics["open_interest"] = _status("unavailable", [], open_interest_hist)

    premium = _request_json("/fapi/v1/premiumIndex", {"symbol": symbol}, timeout)
    if isinstance(premium, dict) and "markPrice" in premium:
        mark = _to_float(premium.get("markPrice"))
        index = _to_float(premium.get("indexPrice"))
        value = None if mark is None or index in {None, 0.0} else (mark / index) - 1.0
        metric_rows = [
            _record(
                timestamp=premium.get("time"),
                source="binance",
                symbol=symbol,
                metric_name="premium",
                metric_value=value,
                delay_ms=0,
            )
        ]
        rows.extend(metric_rows)
        metrics["premium"] = _status("available", metric_rows, {"limitation": "current_snapshot"})
    else:
        metrics["premium"] = _status("unavailable", [], premium)

    taker = _request_json(
        "/futures/data/takerlongshortRatio",
        {"symbol": symbol, "period": "4h", "limit": 500},
        timeout,
    )
    if isinstance(taker, list):
        metric_rows = []
        for item in taker:
            metric_rows.extend(
                [
                    _record(
                        timestamp=item.get("timestamp"),
                        source="binance",
                        symbol=symbol,
                        metric_name="taker_buy_sell_ratio",
                        metric_value=item.get("buySellRatio"),
                        delay_ms=0,
                    ),
                    _record(
                        timestamp=item.get("timestamp"),
                        source="binance",
                        symbol=symbol,
                        metric_name="taker_buy_volume",
                        metric_value=item.get("buyVol"),
                        delay_ms=0,
                    ),
                    _record(
                        timestamp=item.get("timestamp"),
                        source="binance",
                        symbol=symbol,
                        metric_name="taker_sell_volume",
                        metric_value=item.get("sellVol"),
                        delay_ms=0,
                    ),
                ]
            )
        rows.extend(metric_rows)
        metrics["taker_buy_sell"] = _status("available", metric_rows)
    else:
        metrics["taker_buy_sell"] = _status("unavailable", [], taker)

    long_short = _request_json(
        "/futures/data/globalLongShortAccountRatio",
        {"symbol": symbol, "period": "4h", "limit": 500},
        timeout,
    )
    if isinstance(long_short, list):
        metric_rows = [
            _record(
                timestamp=item.get("timestamp"),
                source="binance",
                symbol=symbol,
                metric_name="long_short_ratio",
                metric_value=item.get("longShortRatio"),
                delay_ms=0,
            )
            for item in long_short
        ]
        rows.extend(metric_rows)
        metrics["long_short_ratio"] = _status(
            "history_limited",
            metric_rows,
            {"limitation": "public endpoint has limited historical depth"},
        )
    else:
        metrics["long_short_ratio"] = _status("history_limited", [], long_short)

    metrics["liquidations"] = _status(
        "requires_api_key",
        [],
        {"limitation": "complete historical liquidations require a dedicated provider"},
    )
    return {"source": "binance", "symbol": symbol, "rows": rows, "metrics": metrics}


def _request_json(path: str, params: dict[str, Any], timeout: int) -> Any:
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": type(exc).__name__}


def _request_paginated_funding(
    symbol: str,
    start_ms: int,
    end_ms: int,
    timeout: int,
) -> list[dict[str, Any]] | dict[str, Any]:
    rows: list[dict[str, Any]] = []
    cursor = start_ms
    while cursor < end_ms:
        payload = _request_json(
            "/fapi/v1/fundingRate",
            {"symbol": symbol, "startTime": cursor, "endTime": end_ms, "limit": 1000},
            timeout,
        )
        if not isinstance(payload, list):
            return payload
        if not payload:
            break
        rows.extend(payload)
        last_time = max(int(item.get("fundingTime", cursor)) for item in payload)
        next_cursor = last_time + 1
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        if len(payload) < 1000:
            break
    return rows


def _record(
    *,
    timestamp: Any,
    source: str,
    symbol: str,
    metric_name: str,
    metric_value: Any,
    delay_ms: int,
) -> dict[str, Any]:
    ts = _iso_ms(timestamp)
    return {
        "timestamp": ts,
        "available_timestamp": _iso_ms(None if timestamp is None else int(timestamp) + delay_ms),
        "source": source,
        "symbol": symbol,
        "metric_name": metric_name,
        "metric_value": _to_float(metric_value),
        "metadata_json": "{}",
    }


def _iso_ms(value: Any) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC).isoformat()


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _status(status: str, rows: list[dict[str, Any]], detail: Any | None = None) -> dict[str, Any]:
    timestamps = [item["timestamp"] for item in rows if item.get("timestamp")]
    return {
        "status": status,
        "rows": len(rows),
        "start_timestamp": min(timestamps) if timestamps else None,
        "end_timestamp": max(timestamps) if timestamps else None,
        "known_limitations": detail,
    }
