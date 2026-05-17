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
    base = Path("data/silver/derivatives")
    files = list(base.glob(f"*/{args.symbol}/*")) if base.exists() else []
    payload = {
        "version": "V1.12",
        "symbol": args.symbol,
        "files_found": len(files),
        "status": "available" if files else "unavailable",
        "coverage_note": "Aucun gros fetch obligatoire; coverage local uniquement.",
    }
    write_research_report(
        name="derivatives_readiness_v1_12",
        payload=payload,
        title="Derivatives Coverage V1.12",
        lines=[f"Status: {payload['status']}.", "Coverage derivees locale."],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
