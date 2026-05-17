from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.derivatives.binance_futures import (
    build_binance_futures_plan,
    fetch_binance_public_derivatives,
)
from galapagos.data.derivatives.bybit_v5 import build_bybit_v5_plan, fetch_bybit_public_derivatives
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["binance", "bybit"], required=True)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    plan = (
        build_binance_futures_plan(args.symbol, args.days)
        if args.source == "binance"
        else build_bybit_v5_plan(args.symbol, args.days)
    )
    rows = []
    metrics = {}
    if not args.dry_run:
        result = (
            fetch_binance_public_derivatives(args.symbol, args.days)
            if args.source == "binance"
            else fetch_bybit_public_derivatives(args.symbol, args.days)
        )
        rows = result["rows"]
        metrics = result["metrics"]
        output = Path("data/silver/derivatives") / args.source / args.symbol
        output.mkdir(parents=True, exist_ok=True)
        if rows:
            import pandas as pd

            frame = pd.DataFrame(rows).dropna(subset=["timestamp", "metric_name"])
            for metric_name, metric_frame in frame.groupby("metric_name"):
                metric_frame.to_csv(output / f"{metric_name}.csv", index=False)
    payload = {
        "version": "V1.14",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source": args.source,
        "symbol": args.symbol,
        "days": args.days,
        "dry_run": args.dry_run,
        "network_called": not args.dry_run,
        "status": "planned" if args.dry_run else ("available" if rows else "unavailable"),
        "rows": len(rows),
        "metrics": metrics,
        "plan": plan,
    }
    if not args.dry_run:
        write_research_report(
            name=f"derivatives_fetch_{args.source}_v1_14",
            payload=payload,
            title=f"Derivatives Fetch {args.source} V1.14",
            lines=[
                f"Source: {args.source}.",
                f"Lignes: {len(rows)}.",
                f"Status: {payload['status']}.",
            ],
        )
        collection_path = Path("reports/research/derivatives_collection_v1_14.json")
        existing = {"version": "V1.14", "sources": {}}
        if collection_path.exists():
            existing = json.loads(collection_path.read_text(encoding="utf-8"))
        existing["sources"][args.source] = payload
        write_research_report(
            name="derivatives_collection_v1_14",
            payload=existing,
            title="Derivatives Collection V1.14",
            lines=[
                "Collecte publique controlee Binance/Bybit.",
                f"Sources collectees: {', '.join(sorted(existing['sources']))}.",
                "Les endpoints limites restent marques history_limited/unavailable.",
            ],
        )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
