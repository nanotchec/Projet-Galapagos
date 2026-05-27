from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_batch_expansion_v9_21 import (
    ALLOWED_MODES,
    BATCH_END,
    BATCH_START,
    run_aggtrades_post_v9_batch_expansion_v9_21,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=sorted(ALLOWED_MODES), default="dry-run")
    parser.add_argument("--start-date", default=BATCH_START)
    parser.add_argument("--end-date", default=BATCH_END)
    parser.add_argument("--max-downloads", type=int, default=None)
    args = parser.parse_args()
    report = run_aggtrades_post_v9_batch_expansion_v9_21(
        Path("."),
        mode=args.mode,
        start_date=args.start_date,
        end_date=args.end_date,
        max_downloads=args.max_downloads,
    )
    summary = report["batch_validation"]["summary"]
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "mode": report["mode"],
                "decision": report["v9_21_decision"]["decision"],
                "batch_start": report["batch_window"]["start"],
                "batch_end": report["batch_window"]["end"],
                "max_downloads": report["batch_window"]["max_downloads"],
                "days_requested": summary["days_requested"],
                "days_attempted": summary["days_attempted"],
                "days_downloaded": summary["days_downloaded"],
                "days_normalized": summary["days_normalized"],
                "days_skipped_existing": summary["days_skipped_existing"],
                "days_complete": summary["days_complete"],
                "days_failed": summary["days_failed"],
                "total_rows": summary["total_rows"],
                "raw_bytes_total": summary["raw_bytes_total"],
                "silver_bytes_total": summary["silver_bytes_total"],
                "runtime_seconds": summary["runtime_seconds"],
                "cumulative_known_coverage_start": summary["cumulative_known_coverage_start"],
                "cumulative_known_coverage_end": summary["cumulative_known_coverage_end"],
                "network_used": report["network_used"],
                "api_key_used": report["safety_flags"]["api_key_used"],
                "private_endpoint_used": report["safety_flags"]["private_endpoint_used"],
                "exchange_auth_used": report["safety_flags"]["exchange_auth_used"],
                "websocket_live_used": report["safety_flags"]["websocket_live_used"],
                "complete_collection_reached": report["complete_collection_reached"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
