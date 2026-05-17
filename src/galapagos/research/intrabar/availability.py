"""Check intrabar data availability on public endpoints."""
from __future__ import annotations

from typing import Any

import requests


def check_binance_availability(symbol: str, timeframe: str) -> dict[str, Any]:
    """Check Binance public API for klines availability."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": timeframe, "limit": 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200 and len(response.json()) > 0:
            return {
                "status": "available",
                "source": "binance",
                "symbol": symbol,
                "timeframe": timeframe,
                "max_rows_per_call": 1000,
                "requires_key": False,
                "notes": "Binance public endpoint responds successfully.",
            }
        else:
            return {
                "status": "unavailable",
                "source": "binance",
                "symbol": symbol,
                "timeframe": timeframe,
                "max_rows_per_call": 0,
                "requires_key": False,
                "notes": f"HTTP {response.status_code}: {response.text}",
            }
    except Exception as e:
        return {
            "status": "unavailable",
            "source": "binance",
            "symbol": symbol,
            "timeframe": timeframe,
            "max_rows_per_call": 0,
            "requires_key": False,
            "notes": f"Request failed: {str(e)}",
        }


def check_bybit_availability(symbol: str, timeframe: str) -> dict[str, Any]:
    """Check Bybit public API for klines availability."""
    # Bybit uses minutes for intervals: 1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, M, W
    interval = timeframe.replace("m", "")
    url = "https://api.bybit.com/v5/market/kline"
    params = {"category": "linear", "symbol": symbol, "interval": interval, "limit": 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("retCode") == 0 and data.get("result", {}).get("list"):
                return {
                    "status": "available",
                    "source": "bybit",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "max_rows_per_call": 1000,
                    "requires_key": False,
                    "notes": "Bybit public endpoint responds successfully.",
                }
            else:
                return {
                    "status": "unavailable",
                    "source": "bybit",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "max_rows_per_call": 0,
                    "requires_key": False,
                    "notes": f"Bybit API error: {data.get('retMsg')}",
                }
        else:
            return {
                "status": "unavailable",
                "source": "bybit",
                "symbol": symbol,
                "timeframe": timeframe,
                "max_rows_per_call": 0,
                "requires_key": False,
                "notes": f"HTTP {response.status_code}",
            }
    except Exception as e:
        return {
            "status": "unavailable",
            "source": "bybit",
            "symbol": symbol,
            "timeframe": timeframe,
            "max_rows_per_call": 0,
            "requires_key": False,
            "notes": f"Request failed: {str(e)}",
        }


def check_availability(
    sources: list[str], symbol: str, timeframes: list[str], dry_run: bool = False
) -> list[dict[str, Any]]:
    """Check availability across sources and timeframes."""
    results = []
    for source in sources:
        for tf in timeframes:
            if dry_run:
                results.append(
                    {
                        "status": "dry_run_only",
                        "source": source,
                        "symbol": symbol,
                        "timeframe": tf,
                        "max_rows_per_call": 1000,
                        "requires_key": False,
                        "notes": "Dry run mode.",
                        "recommended_for_v1_18": source == "binance" and tf == "5m",
                    }
                )
                continue

            if source == "binance":
                res = check_binance_availability(symbol, tf)
            elif source == "bybit":
                res = check_bybit_availability(symbol, tf)
            else:
                res = {
                    "status": "not_supported",
                    "source": source,
                    "symbol": symbol,
                    "timeframe": tf,
                    "max_rows_per_call": 0,
                    "requires_key": False,
                    "notes": "Source not supported.",
                }

            # Recommendation logic
            res["recommended_for_v1_18"] = (
                res["status"] == "available" and source == "binance" and tf == "5m"
            )
            results.append(res)
    return results
