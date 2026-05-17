from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

import pandas as pd

from galapagos.data.binance_public_archive import (
    parse_binance_kline_zip,
    plan_binance_ohlcv_download,
)
from galapagos.data.manifest import create_manifest, write_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--market", default="futures_um")
    parser.add_argument("--interval", default="4h")
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-files", type=int, default=0)
    args = parser.parse_args()
    dry_run = args.dry_run
    plans = plan_binance_ohlcv_download(
        symbol=args.symbol,
        market=args.market,
        interval=args.interval,
        years=args.years,
    )
    downloaded = []
    unavailable = []
    combined_rows = 0
    combined_path = (
        Path("data/silver/ohlcv/binance")
        / args.symbol
        / args.interval
        / f"{args.symbol}_{args.interval}_combined.csv"
    )
    if not dry_run:
        frames = []
        selected = plans[: args.max_files] if args.max_files > 0 else plans
        for plan in selected:
            plan.raw_path.parent.mkdir(parents=True, exist_ok=True)
            plan.silver_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                if not plan.raw_path.exists():
                    urllib.request.urlretrieve(plan.url, plan.raw_path)
                frame = parse_binance_kline_zip(plan.raw_path)
                frame.to_csv(plan.silver_path, index=False)
                frames.append(frame)
                downloaded.append(plan.to_dict())
            except urllib.error.HTTPError as exc:
                unavailable.append({**plan.to_dict(), "error": f"HTTP {exc.code}"})
            except Exception as exc:
                unavailable.append({**plan.to_dict(), "error": type(exc).__name__})
        if frames:
            combined = (
                pd.concat(frames, ignore_index=True)
                .sort_values("timestamp")
                .drop_duplicates("timestamp")
            )
            combined.to_csv(combined_path, index=False)
            combined_rows = int(len(combined))
            manifest = create_manifest(
                dataset_id=f"binance_public_{args.symbol}_{args.interval}_v1_12_1",
                source="binance_public_archive",
                symbol=args.symbol,
                timeframe=args.interval,
                file_path=combined_path,
                rows=combined_rows,
                start_timestamp=str(combined["timestamp"].min()),
                end_timestamp=str(combined["timestamp"].max()),
                source_url_or_endpoint="https://data.binance.vision",
                request_params={
                    "symbol": args.symbol,
                    "market": args.market,
                    "interval": args.interval,
                    "years": args.years,
                },
                quality_status="available",
            )
            write_manifest(manifest)
    payload = {
        "version": "V1.12",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "dry_run": dry_run,
        "download_started": not dry_run,
        "status": "dry_run_only" if dry_run else ("available" if combined_rows else "unavailable"),
        "planned_files": len(plans),
        "downloaded_files": len(downloaded),
        "unavailable_files": len(unavailable),
        "combined_rows": combined_rows,
        "combined_path": str(combined_path),
        "unavailable_preview": unavailable[:5],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
