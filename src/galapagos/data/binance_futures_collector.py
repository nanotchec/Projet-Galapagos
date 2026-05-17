from __future__ import annotations

from typing import Any

from galapagos.utils.time_utils import utc_now_iso

DERIVATIVE_FEATURES = [
    "funding",
    "funding_previous",
    "open_interest",
    "open_interest_change",
    "long_short_ratio",
    "basis",
    "liquidations",
]


class BinanceFuturesCollector:
    def __init__(self) -> None:
        import ccxt

        self.exchange = ccxt.binanceusdm({"enableRateLimit": True})

    def fetch_derivatives_snapshot(self, symbol: str) -> dict[str, Any]:
        snapshot = {
            "provider": "binance_futures",
            "symbol": symbol,
            "collected_at_utc": utc_now_iso(),
            "funding": self._fetch_funding(symbol),
            "funding_previous": self._fetch_previous_funding(symbol),
            "open_interest": self._fetch_open_interest(symbol),
            "open_interest_change": self._not_supported(
                symbol,
                "open_interest_change",
                "requires historical open-interest endpoint not integrated in V1.4",
            ),
            "long_short_ratio": self._not_supported(
                symbol,
                "long_short_ratio",
                "requires Binance futures globalLongShortAccountRatio endpoint",
            ),
            "basis": self._not_supported(
                symbol,
                "basis",
                "requires paired spot/perp pricing endpoint; unavailable_in_v1_4",
            ),
            "liquidations": self._not_supported(
                symbol,
                "liquidations",
                "requires liquidation endpoint; unavailable_in_v1_4",
            ),
        }
        return snapshot

    def _fetch_funding(self, symbol: str) -> dict[str, Any]:
        try:
            funding = self.exchange.fetch_funding_rate(symbol)
            return self._available(
                symbol,
                "funding",
                funding.get("fundingRate"),
                source_timestamp=funding.get("timestamp"),
                extra={"raw": funding},
            )
        except Exception as exc:  # noqa: BLE001
            return self._error(symbol, "funding", exc)

    def _fetch_previous_funding(self, symbol: str) -> dict[str, Any]:
        try:
            rows = self.exchange.fetch_funding_rate_history(symbol, limit=2)
            if not rows:
                return self._unavailable(symbol, "funding_previous", "No funding history returned")
            previous = rows[-2] if len(rows) > 1 else rows[-1]
            return self._available(
                symbol,
                "funding_previous",
                previous.get("fundingRate"),
                source_timestamp=previous.get("timestamp"),
                extra={"supported_by_ccxt": True},
            )
        except Exception as exc:  # noqa: BLE001
            return self._error(symbol, "funding_previous", exc)

    def _fetch_open_interest(self, symbol: str) -> dict[str, Any]:
        try:
            oi = self.exchange.fetch_open_interest(symbol)
            return self._available(
                symbol,
                "open_interest",
                oi.get("openInterestAmount") or oi.get("openInterestValue"),
                source_timestamp=oi.get("timestamp"),
                extra={"raw": oi},
            )
        except Exception as exc:  # noqa: BLE001
            return self._error(symbol, "open_interest", exc)

    def _available(
        self,
        symbol: str,
        feature: str,
        value: Any,
        *,
        source_timestamp: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "value": value,
            "status": "available" if value is not None else "unavailable",
            "source": "binance_futures_ccxt",
            "source_timestamp": source_timestamp,
            "collected_at_utc": utc_now_iso(),
            "error_message": None,
            "symbol": symbol,
            "feature": feature,
            **(extra or {}),
        }

    def _error(self, symbol: str, feature: str, exc: Exception) -> dict[str, Any]:
        return {
            "value": None,
            "status": "error",
            "source": "binance_futures_ccxt",
            "source_timestamp": None,
            "collected_at_utc": utc_now_iso(),
            "error_message": str(exc),
            "symbol": symbol,
            "feature": feature,
            "supported_by_ccxt": True,
        }

    def _unavailable(self, symbol: str, feature: str, message: str) -> dict[str, Any]:
        return {
            "value": None,
            "status": "unavailable",
            "source": "binance_futures_ccxt",
            "source_timestamp": None,
            "collected_at_utc": utc_now_iso(),
            "error_message": message,
            "symbol": symbol,
            "feature": feature,
        }

    def _not_supported(self, symbol: str, feature: str, message: str) -> dict[str, Any]:
        return {
            "value": None,
            "status": "not_supported",
            "source": "binance_futures",
            "source_timestamp": None,
            "collected_at_utc": utc_now_iso(),
            "error_message": message,
            "symbol": symbol,
            "feature": feature,
            "supported_by_ccxt": False,
            "requires_exchange_endpoint": True,
            "unavailable_in_v1_4": True,
        }


def unavailable_derivatives(symbol: str) -> dict[str, Any]:
    return {
        "provider": "mock_status",
        "symbol": symbol,
        "collected_at_utc": utc_now_iso(),
        **{
            feature: {
                "value": None,
                "status": "unavailable",
                "source": "mock_status",
                "source_timestamp": None,
                "collected_at_utc": utc_now_iso(),
                "error_message": "Mock/no real derivatives data collected",
                "symbol": symbol,
                "feature": feature,
            }
            for feature in DERIVATIVE_FEATURES
        },
    }


def derivatives_availability_summary(derivatives: dict[str, Any]) -> dict[str, str]:
    return {
        feature: payload.get("status", "missing")
        for feature, payload in derivatives.items()
        if isinstance(payload, dict)
    }


def unavailable_features(derivatives: dict[str, Any]) -> list[str]:
    return [
        feature
        for feature, status in derivatives_availability_summary(derivatives).items()
        if status != "available"
    ]
