from __future__ import annotations

import io
import json
import re
import uuid
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from galapagos.data.public_market.config import ALLOWED_PUBLIC_HOSTS
from galapagos.data.public_market.provenance import sha256_file, utc_now_iso


VERSION_V5_0 = "V5.0"
SYMBOL_V5_0 = "BTCUSDT"
SOURCE_TIMEFRAME_V5_0 = "1m"
SOURCE_MARKET_TYPE_V5_0 = "spot"
BINANCE_PUBLIC_HOST_V5_0 = "data.binance.vision"
S3_BUCKET_LIST_URL_V5_0 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
S3_PREFIX_V5_0 = "data/spot/daily/klines/BTCUSDT/1m/"
RAW_ROWS_PER_COMPLETE_DAY_V5_0 = 1440
DISCOVERY_JSON_PATH_V5_0 = Path("reports/data_quality/max_history_public_market_data_v5_0_discovery.json")
DISCOVERY_MD_PATH_V5_0 = Path("reports/data_quality/max_history_public_market_data_v5_0_discovery.md")
EXPECTED_LIMITATIONS_DISCOVERY_V5_0 = [
    "V5.0 decouvre uniquement les archives publiques OHLCV BTCUSDT 1m disponibles sur Binance public archive.",
    "V5.0 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.",
]

_ZIP_DATE_PATTERN = re.compile(r"BTCUSDT-1m-(\d{4}-\d{2}-\d{2})\.zip$")


def discover_max_history_public_market_data_v5_0(
    root: Path = Path("."),
    *,
    no_network: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
    allow_documented_gaps: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    created_at = utc_now_iso()
    discovery_run_id = f"v5_0_discovery_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"

    if no_network:
        raw_dates = list_local_raw_dates_v5_0(root)
        discovery_mode = "local_raw_files"
    else:
        raw_dates = discover_remote_daily_zip_dates_v5_0()
        discovery_mode = "binance_public_s3_listing"

    if not raw_dates:
        payload = _empty_discovery(created_at, discovery_run_id, discovery_mode, allow_documented_gaps)
        payload["status"] = "FAIL"
        payload["errors"] = ["no BTCUSDT 1m daily zip found"]
        _write_discovery_outputs(root, payload)
        return payload

    first_available = raw_dates[0]
    last_available = _drop_future_or_current_dates(raw_dates)[-1]
    complete_start = _first_complete_date(root, raw_dates, no_network=no_network)
    complete_end = _last_complete_date(root, _drop_future_or_current_dates(raw_dates), no_network=no_network)
    window_start = start_date or complete_start
    window_end = end_date or complete_end
    retained_dates = _date_range(window_start, window_end)
    available_set = set(raw_dates)
    missing_dates = [item for item in retained_dates if item not in available_set]
    errors = []
    if date.fromisoformat(window_start) > date.fromisoformat(window_end):
        errors.append("window_start must be <= window_end")
    if missing_dates and not allow_documented_gaps:
        errors.append("missing dates detected in max-history archive window")

    payload = {
        "version": VERSION_V5_0,
        "status": "PASS" if not errors else "FAIL",
        "created_at_utc": created_at,
        "discovery_run_id": discovery_run_id,
        "discovery_mode": discovery_mode,
        "source": _source_payload(),
        "first_available_date": first_available,
        "last_available_date": last_available,
        "first_complete_date": complete_start,
        "last_complete_date": complete_end,
        "window_start": window_start,
        "window_end": window_end,
        "total_days": len(retained_dates),
        "expected_raw_files": len(retained_dates),
        "available_zip_dates_count": len(raw_dates),
        "missing_dates": missing_dates,
        "documented_gaps_allowed": bool(allow_documented_gaps),
        "retained_dates_preview": {
            "first_5": retained_dates[:5],
            "last_5": retained_dates[-5:],
        },
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_DISCOVERY_V5_0,
        "errors": errors,
        "warnings": [],
    }
    _write_discovery_outputs(root, payload)
    return payload


def discover_remote_daily_zip_dates_v5_0(timeout_seconds: int = 60) -> list[str]:
    marker: str | None = None
    keys: list[str] = []
    while True:
        params = {"delimiter": "/", "prefix": S3_PREFIX_V5_0}
        if marker:
            params["marker"] = marker
        url = f"{S3_BUCKET_LIST_URL_V5_0}?{urlencode(params)}"
        _validate_public_listing_url(url)
        request = Request(url, headers={"User-Agent": "galapagos-v5.0-public-read-only"})
        with urlopen(request, timeout=timeout_seconds) as response:
            if getattr(response, "status", 200) != 200:
                raise RuntimeError(f"public archive listing failed with status {response.status}")
            root = ET.fromstring(response.read())
        page_keys = [node.text or "" for node in root.findall(".//{*}Key")]
        keys.extend(page_keys)
        truncated = (root.findtext(".//{*}IsTruncated") or "").casefold() == "true"
        marker = root.findtext(".//{*}NextMarker") or (page_keys[-1] if page_keys else None)
        if not truncated:
            break
        if marker is None:
            raise RuntimeError("public archive listing was truncated without a pagination marker")
    dates = sorted(
        match.group(1)
        for key in keys
        if (match := _ZIP_DATE_PATTERN.search(key)) is not None
    )
    return dates


def list_local_raw_dates_v5_0(root: Path = Path(".")) -> list[str]:
    raw_dir = raw_dir_v5_0(root.resolve())
    return sorted(
        match.group(1)
        for path in raw_dir.glob("BTCUSDT-1m-*.zip")
        if (match := _ZIP_DATE_PATTERN.match(path.name)) is not None
    )


def raw_dir_v5_0(root: Path) -> Path:
    return root / "data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m"


def raw_zip_path_v5_0(root: Path, current_date: str) -> Path:
    return raw_dir_v5_0(root) / f"BTCUSDT-1m-{current_date}.zip"


def build_public_archive_url_v5_0(current_date: str) -> str:
    return (
        f"https://{BINANCE_PUBLIC_HOST_V5_0}/data/spot/daily/klines/"
        f"{SYMBOL_V5_0}/{SOURCE_TIMEFRAME_V5_0}/{SYMBOL_V5_0}-{SOURCE_TIMEFRAME_V5_0}-{current_date}.zip"
    )


def load_discovery_v5_0(root: Path = Path(".")) -> dict[str, Any]:
    return json.loads((root.resolve() / DISCOVERY_JSON_PATH_V5_0).read_text(encoding="utf-8"))


def expected_rows_from_days_v5_0(days: int) -> dict[str, int]:
    return {"1m": days * 1440, "5m": days * 288, "15m": days * 96, "1h": days * 24}


def dates_from_discovery_v5_0(discovery: dict[str, Any]) -> list[str]:
    return _date_range(discovery["window_start"], discovery["window_end"])


def _first_complete_date(root: Path, raw_dates: list[str], *, no_network: bool) -> str:
    for current_date in raw_dates:
        if _raw_daily_row_count(root, current_date, no_network=no_network) == RAW_ROWS_PER_COMPLETE_DAY_V5_0:
            return current_date
    raise RuntimeError("no complete first date found in BTCUSDT 1m archive")


def _last_complete_date(root: Path, raw_dates: list[str], *, no_network: bool) -> str:
    for current_date in reversed(raw_dates):
        if _raw_daily_row_count(root, current_date, no_network=no_network) == RAW_ROWS_PER_COMPLETE_DAY_V5_0:
            return current_date
    raise RuntimeError("no complete last date found in BTCUSDT 1m archive")


def _raw_daily_row_count(root: Path, current_date: str, *, no_network: bool) -> int:
    path = raw_zip_path_v5_0(root, current_date)
    if path.exists():
        return count_binance_kline_zip_rows_fast_v5_0(path)
    if no_network:
        return -1
    url = build_public_archive_url_v5_0(current_date)
    _validate_public_archive_url(url)
    request = Request(url, headers={"User-Agent": "galapagos-v5.0-public-read-only"})
    with urlopen(request, timeout=60) as response:
        if getattr(response, "status", 200) != 200:
            return -1
        return count_binance_kline_zip_rows_bytes_v5_0(response.read())


def count_binance_kline_zip_rows_fast_v5_0(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"expected one CSV member, found {len(csv_names)}")
        with archive.open(csv_names[0], "r") as handle:
            return _count_non_empty_csv_rows(handle)


def count_binance_kline_zip_rows_bytes_v5_0(content: bytes) -> int:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"expected one CSV member, found {len(csv_names)}")
        with archive.open(csv_names[0], "r") as handle:
            return _count_non_empty_csv_rows(handle)


def build_raw_file_inventory_entry_v5_0(root: Path, current_date: str, rows: int | None = None) -> dict[str, Any]:
    path = raw_zip_path_v5_0(root, current_date)
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(rows if rows is not None else count_binance_kline_zip_rows_fast_v5_0(path)),
    }


def _count_non_empty_csv_rows(handle: Any) -> int:
    count = 0
    first_non_empty: bytes | None = None
    for raw_line in handle:
        line = raw_line.strip()
        if not line:
            continue
        if first_non_empty is None:
            first_non_empty = line
        count += 1
    if first_non_empty is None:
        return 0
    first_token = first_non_empty.split(b",", 1)[0].strip().lower()
    if first_token in {b"open_time", b"timestamp", b"date"}:
        count -= 1
    return count


def _date_range(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range((end_date - start_date).days + 1)]


def _drop_future_or_current_dates(raw_dates: list[str]) -> list[str]:
    last_complete_allowed = datetime.now(UTC).date() - timedelta(days=1)
    return [item for item in raw_dates if date.fromisoformat(item) <= last_complete_allowed]


def _validate_public_listing_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "s3-ap-northeast-1.amazonaws.com":
        raise ValueError("V5.0 discovery only allows Binance public S3 listing.")


def _validate_public_archive_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_PUBLIC_HOSTS:
        raise ValueError("V5.0 allows public read-only downloads from data.binance.vision only.")


def _source_payload() -> dict[str, str]:
    return {
        "name": "binance_public_archive",
        "venue": "binance",
        "market_type": SOURCE_MARKET_TYPE_V5_0,
        "symbol": SYMBOL_V5_0,
        "source_timeframe": SOURCE_TIMEFRAME_V5_0,
        "host": BINANCE_PUBLIC_HOST_V5_0,
    }


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


def _empty_discovery(
    created_at: str,
    discovery_run_id: str,
    discovery_mode: str,
    allow_documented_gaps: bool,
) -> dict[str, Any]:
    return {
        "version": VERSION_V5_0,
        "status": "FAIL",
        "created_at_utc": created_at,
        "discovery_run_id": discovery_run_id,
        "discovery_mode": discovery_mode,
        "source": _source_payload(),
        "first_available_date": None,
        "last_available_date": None,
        "first_complete_date": None,
        "last_complete_date": None,
        "window_start": None,
        "window_end": None,
        "total_days": 0,
        "expected_raw_files": 0,
        "available_zip_dates_count": 0,
        "missing_dates": [],
        "documented_gaps_allowed": bool(allow_documented_gaps),
        "retained_dates_preview": {"first_5": [], "last_5": []},
        "safety": _safety(),
        "limitations": EXPECTED_LIMITATIONS_DISCOVERY_V5_0,
        "errors": [],
        "warnings": [],
    }


def _write_discovery_outputs(root: Path, payload: dict[str, Any]) -> None:
    _write_json(root / DISCOVERY_JSON_PATH_V5_0, payload)
    _write_text(root / DISCOVERY_MD_PATH_V5_0, build_discovery_markdown_v5_0(payload))


def build_discovery_markdown_v5_0(payload: dict[str, Any]) -> str:
    errors = "\n".join(f"- {item}" for item in payload.get("errors", [])) or "- Aucune"
    missing = "\n".join(f"- {item}" for item in payload.get("missing_dates", [])[:50]) or "- Aucune"
    incomplete = "\n".join(f"- {item}" for item in payload.get("incomplete_dates_excluded", [])[:50]) or "- Aucune"
    limitations = "\n".join(f"- {item}" for item in payload["limitations"])
    return f"""# Discovery OHLCV historique max V5.0

## Statut

- Statut : `{payload['status']}`
- Mode : `{payload['discovery_mode']}`
- Premiere date disponible : `{payload['first_available_date']}`
- Derniere date disponible : `{payload['last_available_date']}`
- Premiere date complete retenable : `{payload['first_complete_date']}`
- Derniere date complete retenable : `{payload['last_complete_date']}`
- Fenetre retenue : `{payload['window_start']}` -> `{payload['window_end']}`
- Nombre de jours retenus : `{payload['total_days']}`
- Raw zips attendus : `{payload['expected_raw_files']}`
- Gaps documentes autorises : `{payload['documented_gaps_allowed']}`

## Dates manquantes

{missing}

## Dates incompletes exclues

{incomplete}

## Erreurs

{errors}

## Limitations

{limitations}

## Securite

V5.0 utilise uniquement des endpoints publics read-only.
V5.0 ne valide aucune strategie.
V5.0 ne produit aucune feature.
V5.0 ne produit aucun label.
V5.0 ne produit aucun dataset ML.
V5.0 ne produit aucun modele ML.
V5.0 ne produit aucun backtest.
V5.0 ne produit aucun signal de trading.
V5.0 ne produit aucun ordre.
V5.0 n'autorise aucun paper live.
V5.0 n'autorise aucun trading reel.
"""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
