from __future__ import annotations

import json
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from galapagos.data.public_trades.config import (
    ALLOWED_PUBLIC_HOSTS,
    BINANCE_PUBLIC_HOST,
    DEFAULT_PREVIEW_DAYS,
    DISCOVERY_JSON_PATH_V7_0,
    DISCOVERY_MD_PATH_V7_0,
    MARKET_TYPE,
    SOURCE_NAME,
    SYMBOL,
    TRADE_SOURCE_TYPE,
    V5_0_MANIFEST_PATH,
    VENUE,
    VERSION_V7_0,
    raw_zip_path,
)
from galapagos.data.public_trades.provenance import sha256_file, utc_now_iso


def build_public_trades_archive_url(*, date_value: str, trade_source_type: str = TRADE_SOURCE_TYPE) -> str:
    if trade_source_type not in {"aggTrades", "trades"}:
        raise ValueError("V7.0 supports Binance public aggTrades or trades archives only.")
    return (
        f"https://{BINANCE_PUBLIC_HOST}/data/spot/daily/{trade_source_type}/"
        f"{SYMBOL}/{SYMBOL}-{trade_source_type}-{date_value}.zip"
    )


def discover_public_trades_v7_0(
    root: Path = Path("."),
    *,
    preview_days: int = DEFAULT_PREVIEW_DAYS,
    start_date: str | None = None,
    end_date: str | None = None,
    allow_documented_gaps: bool = False,
    download_raw: bool = True,
) -> dict:
    root = root.resolve()
    if preview_days < 1:
        raise ValueError("preview_days must be positive")
    v5_manifest = _read_json(root / V5_0_MANIFEST_PATH)
    v5_window_start = v5_manifest["discovery"]["window_start"]
    v5_window_end = v5_manifest["discovery"]["window_end"]
    selected_start = start_date or v5_window_start
    selected_end = end_date or _date_add(selected_start, preview_days - 1)
    if selected_start < v5_window_start or selected_end > v5_window_end:
        raise ValueError("V7.0 preview window must remain inside the V5.0 validated OHLCV window.")

    selected_dates = _date_range(selected_start, selected_end)
    available_dates: list[str] = []
    missing_dates: list[str] = []
    remote_files: dict[str, dict] = {}
    for current_date in selected_dates:
        url = build_public_trades_archive_url(date_value=current_date)
        probe = _probe_public_archive(url)
        if probe["available"]:
            available_dates.append(current_date)
            remote_files[current_date] = probe
            if download_raw:
                _download_public_archive(url, raw_zip_path(root, current_date))
        else:
            missing_dates.append(current_date)

    errors = []
    if missing_dates and not allow_documented_gaps:
        errors.append(f"missing aggTrades dates in selected V7.0 window: {missing_dates}")
    raw_inventory = {
        current_date: _raw_inventory_entry(root, current_date)
        for current_date in available_dates
        if raw_zip_path(root, current_date).exists()
    }
    total_days = len(selected_dates)
    matches_v5_0_window = selected_start == v5_window_start and selected_end == v5_window_end
    reason = (
        "full V5.0 window selected"
        if matches_v5_0_window
        else "bounded V7.0 preview window selected because full V5.0 aggTrades history is too large for the first auditable ingestion layer"
    )
    discovery = {
        "version": VERSION_V7_0,
        "status": "PASS" if not errors else "FAIL",
        "created_at_utc": utc_now_iso(),
        "source": {
            "name": "binance_public_archive",
            "venue": VENUE,
            "market_type": MARKET_TYPE,
            "symbol": SYMBOL,
            "trade_source_type": TRADE_SOURCE_TYPE,
            "host": BINANCE_PUBLIC_HOST,
        },
        "first_available_date": available_dates[0] if available_dates else None,
        "last_available_date": available_dates[-1] if available_dates else None,
        "available_dates": available_dates,
        "missing_dates": missing_dates,
        "total_available_days": len(available_dates),
        "source_type": TRADE_SOURCE_TYPE,
        "v5_0_window_start": v5_window_start,
        "v5_0_window_end": v5_window_end,
        "overlap_start": selected_start if available_dates else None,
        "overlap_end": selected_end if available_dates else None,
        "overlap_days": total_days if not missing_dates else len(available_dates),
        "recommended_window": {
            "window_start": selected_start,
            "window_end": selected_end,
            "total_days": total_days,
            "matches_v5_0_window": matches_v5_0_window,
            "reason": reason,
        },
        "remote_files": remote_files,
        "raw_files": raw_inventory,
        "documented_gaps_allowed": allow_documented_gaps,
        "errors": errors,
        "warnings": [] if matches_v5_0_window else [reason],
    }
    _write_json(root / DISCOVERY_JSON_PATH_V7_0, discovery)
    _write_text(root / DISCOVERY_MD_PATH_V7_0, render_discovery_markdown_v7_0(discovery))
    return discovery


def render_discovery_markdown_v7_0(discovery: dict) -> str:
    window = discovery["recommended_window"]
    missing = "\n".join(f"- `{item}`" for item in discovery["missing_dates"]) or "- Aucune"
    raw = "\n".join(
        f"- `{date_key}` : `{payload['path']}`, `{payload['rows']}` lignes, `{payload['bytes']}` octets"
        for date_key, payload in discovery["raw_files"].items()
    ) or "- Aucun"
    warnings = "\n".join(f"- {item}" for item in discovery["warnings"]) or "- Aucune"
    return f"""# Discovery trades publics V7.0

V7.0 decouvre une fenetre preview de trades publics Binance `{discovery['source_type']}` pour `BTCUSDT` spot.

## Fenetre

- Fenetre V5.0 : `{discovery['v5_0_window_start']}` -> `{discovery['v5_0_window_end']}`.
- Fenetre V7.0 retenue : `{window['window_start']}` -> `{window['window_end']}`.
- Total jours V7.0 : `{window['total_days']}`.
- Meme fenetre que V5.0 : `{window['matches_v5_0_window']}`.
- Raison : {window['reason']}.

## Disponibilite

- Premiere date disponible decouverte : `{discovery['first_available_date']}`.
- Derniere date disponible decouverte : `{discovery['last_available_date']}`.
- Jours disponibles : `{discovery['total_available_days']}`.
- Trous documentes autorises : `{discovery['documented_gaps_allowed']}`.

## Dates manquantes

{missing}

## Raw inventory

{raw}

## Avertissements

{warnings}

V7.0 ne produit aucune feature, aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.
"""


def count_agg_trade_zip_rows(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError("Expected exactly one CSV inside Binance aggTrades archive.")
        with archive.open(csv_names[0]) as handle:
            first = handle.readline()
            rows = sum(1 for _ in handle) + (1 if first else 0)
    first_text = first.decode("utf-8", errors="ignore").casefold()
    has_header = any(token in first_text for token in ["agg", "price", "quantity", "trade"])
    return rows - 1 if has_header else rows


def _probe_public_archive(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_PUBLIC_HOSTS:
        raise ValueError("V7.0 allows public read-only access to data.binance.vision only.")
    request = Request(url, method="HEAD", headers={"User-Agent": "galapagos-v7.0-public-read-only"})
    try:
        with urlopen(request, timeout=30) as response:
            return {
                "url": url,
                "available": getattr(response, "status", 200) == 200,
                "content_length": int(response.headers.get("content-length", "0")),
                "last_modified": response.headers.get("last-modified"),
            }
    except HTTPError as exc:
        if exc.code == 404:
            return {"url": url, "available": False, "status": exc.code}
        raise
    except URLError as exc:
        raise RuntimeError(f"public archive probe failed: {exc}") from exc


def _download_public_archive(url: str, destination: Path) -> None:
    if destination.exists():
        return
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in ALLOWED_PUBLIC_HOSTS:
        raise ValueError("V7.0 allows public read-only downloads from data.binance.vision only.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "galapagos-v7.0-public-read-only"})
    with urlopen(request, timeout=120) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"public archive download failed with status {response.status}")
        destination.write_bytes(response.read())


def _raw_inventory_entry(root: Path, current_date: str) -> dict:
    path = raw_zip_path(root, current_date)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": count_agg_trade_zip_rows(path),
    }


def _date_range(start: str, end: str) -> list[str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("end date must be >= start date")
    days = (end_date - start_date).days + 1
    return [(start_date + timedelta(days=offset)).isoformat() for offset in range(days)]


def _date_add(value: str, days: int) -> str:
    return (date.fromisoformat(value) + timedelta(days=days)).isoformat()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
