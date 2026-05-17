from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ReadinessStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_SUPPORTED = "not_supported"
    REQUIRES_API_KEY = "requires_api_key"
    RATE_LIMITED = "rate_limited"
    HISTORY_LIMITED = "history_limited"


@dataclass(frozen=True)
class DerivativesSourceCheck:
    source: str
    dataset: str
    status: ReadinessStatus
    public_no_key: bool
    history_note: str
    requires_env: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def build_derivatives_readiness(symbol: str, *, dry_run: bool = True) -> dict[str, Any]:
    """Return a non-secret readiness matrix for public and optional derivatives data."""
    checks = [
        DerivativesSourceCheck(
            source="binance_futures",
            dataset="funding_rate",
            status=ReadinessStatus.AVAILABLE,
            public_no_key=True,
            history_note="Historique public pagine possible, limites de taux a respecter.",
        ),
        DerivativesSourceCheck(
            source="binance_futures",
            dataset="open_interest",
            status=ReadinessStatus.AVAILABLE,
            public_no_key=True,
            history_note="Snapshot public; historique via endpoint separe selon disponibilite.",
        ),
        DerivativesSourceCheck(
            source="binance_futures",
            dataset="long_short_ratio",
            status=ReadinessStatus.HISTORY_LIMITED,
            public_no_key=True,
            history_note="Historique souvent limite, typiquement court selon endpoint.",
        ),
        DerivativesSourceCheck(
            source="bybit_v5",
            dataset="funding_rate",
            status=ReadinessStatus.AVAILABLE,
            public_no_key=True,
            history_note="Endpoint public V5, pagination future necessaire.",
        ),
        DerivativesSourceCheck(
            source="bybit_v5",
            dataset="open_interest",
            status=ReadinessStatus.AVAILABLE,
            public_no_key=True,
            history_note="Endpoint public V5, couverture a verifier par symbole.",
        ),
        DerivativesSourceCheck(
            source="coinglass",
            dataset="liquidations_funding_oi_etf_flows",
            status=(
                ReadinessStatus.AVAILABLE
                if os.getenv("COINGLASS_API_KEY")
                else ReadinessStatus.REQUIRES_API_KEY
            ),
            public_no_key=False,
            history_note="Provider optionnel; ne pas appeler sans cle API.",
            requires_env="COINGLASS_API_KEY",
        ),
        DerivativesSourceCheck(
            source="fred",
            dataset="macro_rates_liquidity_proxies",
            status=(
                ReadinessStatus.AVAILABLE
                if os.getenv("FRED_API_KEY")
                else ReadinessStatus.REQUIRES_API_KEY
            ),
            public_no_key=False,
            history_note="Macro future optionnelle, pas de contexte live en V1.11.",
            requires_env="FRED_API_KEY",
        ),
    ]
    return {
        "version": "V1.11",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "symbol": symbol,
        "dry_run": dry_run,
        "checks": [check.to_dict() for check in checks],
        "secrets_logged": False,
        "notes": [
            "Les endpoints publics peuvent fonctionner sans cle pour certains jeux.",
            "CoinGlass et FRED restent optionnels tant que les cles ne sont pas fournies.",
            "Aucune cle API ne doit etre logguee.",
        ],
    }


def fetch_public_derivatives_sample(
    *,
    source: str,
    symbol: str,
    limit: int = 10,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    if limit <= 0 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")
    normalized = symbol.replace("/", "").replace(":", "").upper()
    if source == "binance":
        query = urllib.parse.urlencode({"symbol": normalized, "limit": limit})
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?{query}"
    elif source == "bybit":
        query = urllib.parse.urlencode(
            {"category": "linear", "symbol": normalized, "limit": limit}
        )
        url = f"https://api.bybit.com/v5/market/funding/history?{query}"
    else:
        raise ValueError("source must be binance or bybit.")
    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
        parsed = json.loads(body)
        sample_payload = (
            parsed if isinstance(parsed, list) else parsed.get("result", {}).get("list", [])
        )
        sample_count = len(sample_payload)
        return {
            "source": source,
            "symbol": normalized,
            "status": ReadinessStatus.AVAILABLE.value,
            "sample_count": sample_count,
            "payload_preview": parsed if sample_count <= 10 else "sample_truncated",
        }
    except urllib.error.HTTPError as exc:
        status = ReadinessStatus.RATE_LIMITED if exc.code == 429 else ReadinessStatus.UNAVAILABLE
        return {
            "source": source,
            "symbol": normalized,
            "status": status.value,
            "error": f"HTTP {exc.code}",
        }
    except Exception as exc:
        return {
            "source": source,
            "symbol": normalized,
            "status": ReadinessStatus.UNAVAILABLE.value,
            "error": type(exc).__name__,
        }
