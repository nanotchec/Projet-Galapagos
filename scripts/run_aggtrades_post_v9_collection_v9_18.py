from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_collection_v9_18 import ALLOWED_MODES, run_aggtrades_post_v9_collection_v9_18


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=sorted(ALLOWED_MODES), default="dry-run")
    parser.add_argument("--max-downloads", type=int, default=None)
    args = parser.parse_args()
    report = run_aggtrades_post_v9_collection_v9_18(Path("."), mode=args.mode, max_downloads=args.max_downloads)
    coverage = report["coverage_summary"]
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "mode": report["mode"],
                "decision": report["v9_18_decision"]["decision"],
                "days_expected": coverage["days_expected"],
                "days_already_present": coverage["days_already_present"],
                "days_missing": coverage["days_missing"],
                "collection_executed": report["collection_executed"],
                "network_used": report["network_used"],
                "new_data_downloaded": report["new_data_downloaded"],
                "ingestion_executed": report["ingestion_executed"],
                "api_key_used": report["safety_flags"]["api_key_used"],
                "private_endpoint_used": report["safety_flags"]["private_endpoint_used"],
                "websocket_live_used": report["safety_flags"]["websocket_live_used"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
