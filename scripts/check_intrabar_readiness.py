from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    args = parser.parse_args()
    base = Path("data/silver/ohlcv/binance") / args.symbol
    files_5m = list((base / "5m").glob("*")) if (base / "5m").exists() else []
    files_1m = list((base / "1m").glob("*")) if (base / "1m").exists() else []
    payload = {
        "version": "V1.12.2",
        "symbol": args.symbol,
        "five_minute_files": len(files_5m),
        "one_minute_files": len(files_1m),
        "status": "available" if files_5m or files_1m else "unavailable",
        "note": "Aucun telechargement 1m massif sans flag explicite.",
    }
    write_research_report(
        name="intrabar_readiness_v1_12_2",
        payload=payload,
        title="Intrabar Readiness V1.12.2",
        lines=[f"Status: {payload['status']}.", payload["note"]],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
