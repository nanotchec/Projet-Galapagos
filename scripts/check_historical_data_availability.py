from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.backtest.historical_data import find_latest_cached_ohlcv, load_historical_ohlcv
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="4h")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload = check_historical_data(profile=args.profile, dry_run=args.dry_run)
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def check_historical_data(*, profile: str = "4h", dry_run: bool = True) -> dict:
    timeframe = "4h" if profile == "4h" else profile
    silver_path = (
        Path("data/silver/ohlcv/binance/BTCUSDT")
        / timeframe
        / f"BTCUSDT_{timeframe}_combined.csv"
    )
    path = silver_path if silver_path.exists() else find_latest_cached_ohlcv(
        "BTC/USDT:USDT",
        timeframe,
    )
    payload = {
        "version": "V1.11",
        "profile": profile,
        "timeframe": timeframe,
        "dry_run": dry_run,
        "download_started": False,
        "local_path": str(path) if path else None,
        "available": path is not None,
        "bars": 0,
        "start_timestamp": None,
        "end_timestamp": None,
        "missing": [],
    }
    if path:
        data = load_historical_ohlcv(Path(path)) if Path(path).suffix != ".csv" else __import__(
            "pandas"
        ).read_csv(Path(path))
        payload.update(
            {
                "bars": int(len(data)),
                "start_timestamp": str(data["timestamp"].iloc[0]) if not data.empty else None,
                "end_timestamp": str(data["timestamp"].iloc[-1]) if not data.empty else None,
            }
        )
    if payload["bars"] < 365 * 6:
        payload["missing"].append("BTC 4h 3-5 ans recommandé pour recherche robuste.")
    if payload["bars"] < 720:
        payload["missing"].append("Historique local court pour evaluation multi-fenetres.")
    write_research_report(
        name="historical_data_readiness_v1_11",
        payload=payload,
        title="Historical Data Readiness V1.11",
        lines=[
            "Verification locale uniquement; aucun telechargement massif.",
            f"Barres disponibles: {payload['bars']}.",
        ],
    )
    return payload


if __name__ == "__main__":
    main()
