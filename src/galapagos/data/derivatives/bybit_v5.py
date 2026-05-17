from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any

BASE_URL = "https://api.bybit.com/v5"


def build_bybit_v5_plan(symbol: str, days: int) -> dict:
    query = urllib.parse.urlencode({"category": "linear", "symbol": symbol})
    return {
        "symbol": symbol,
        "days": days,
        "funding_rate": f"{BASE_URL}/market/funding/history?{query}",
        "open_interest": f"{BASE_URL}/market/open-interest?{query}",
        "premium_index": f"{BASE_URL}/market/tickers?{query}",
        "long_short_ratio": "not_supported_or_history_limited_public_endpoint",
    }


def fetch_bybit_public_derivatives(symbol: str, days: int, timeout: int = 20) -> dict[str, Any]:
    now = datetime.now(UTC)
    start_ms = int((now - timedelta(days=days)).timestamp() * 1000)
    end_ms = int(now.timestamp() * 1000)
    metrics: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    funding = _request_json(
        "/market/funding/history",
        {
            "category": "linear",
            "symbol": symbol,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 200,
        },
        timeout,
    )
    funding_items = _items(funding)
    if funding_items is not None:
        metric_rows = [
            _record(
                timestamp=item.get("fundingRateTimestamp"),
                source="bybit",
                symbol=symbol,
                metric_name="funding_rate",
                metric_value=item.get("fundingRate"),
            )
            for item in funding_items
        ]
        rows.extend(metric_rows)
        metrics["funding_rate"] = _status("available", metric_rows)
    else:
        metrics["funding_rate"] = _status("unavailable", [], funding)

    oi = _request_json(
        "/market/open-interest",
        {"category": "linear", "symbol": symbol, "intervalTime": "4h", "limit": 200},
        timeout,
    )
    oi_items = _items(oi)
    if oi_items is not None:
        metric_rows = [
            _record(
                timestamp=item.get("timestamp"),
                source="bybit",
                symbol=symbol,
                metric_name="open_interest",
                metric_value=item.get("openInterest"),
            )
            for item in oi_items
        ]
        rows.extend(metric_rows)
        metrics["open_interest"] = _status("available", metric_rows)
    else:
        metrics["open_interest"] = _status("unavailable", [], oi)

    ticker = _request_json(
        "/market/tickers",
        {"category": "linear", "symbol": symbol},
        timeout,
    )
    ticker_items = _items(ticker)
    if ticker_items:
        item = ticker_items[0]
        mark = _to_float(item.get("markPrice"))
        index = _to_float(item.get("indexPrice"))
        value = None if mark is None or index in {None, 0.0} else (mark / index) - 1.0
        metric_rows = [
            _record(
                timestamp=int(datetime.now(UTC).timestamp() * 1000),
                source="bybit",
                symbol=symbol,
                metric_name="premium",
                metric_value=value,
            )
        ]
        rows.extend(metric_rows)
        metrics["premium"] = _status("available", metric_rows, {"limitation": "current_snapshot"})
    else:
        metrics["premium"] = _status("unavailable", [], ticker)

    metrics["taker_buy_sell"] = _status(
        "not_supported",
        [],
        {"limitation": "not exposed in V5 public market endpoint used here"},
    )
    metrics["long_short_ratio"] = _status(
        "not_supported",
        [],
        {"limitation": "not available as long public history in V5 here"},
    )
    metrics["liquidations"] = _status(
        "requires_api_key",
        [],
        {"limitation": "historical liquidation feed requires dedicated provider"},
    )
    return {"source": "bybit", "symbol": symbol, "rows": rows, "metrics": metrics}


def _request_json(path: str, params: dict[str, Any], timeout: int) -> Any:
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": type(exc).__name__}


def _items(payload: Any) -> list[dict[str, Any]] | None:
    if not isinstance(payload, dict):
        return None
    if payload.get("retCode") not in {0, "0", None}:
        return None
    items = payload.get("result", {}).get("list")
    return items if isinstance(items, list) else None


def _record(
    *,
    timestamp: Any,
    source: str,
    symbol: str,
    metric_name: str,
    metric_value: Any,
) -> dict[str, Any]:
    ts = _iso_ms(timestamp)
    return {
        "timestamp": ts,
        "available_timestamp": ts,
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
