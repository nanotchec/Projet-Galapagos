from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_pilot_collection_v9_19 import (
    ALLOWED_MODES,
    PILOT_END,
    PILOT_START,
    run_aggtrades_post_v9_pilot_collection_v9_19,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=sorted(ALLOWED_MODES), default="dry-run")
    parser.add_argument("--start-date", default=PILOT_START)
    parser.add_argument("--end-date", default=PILOT_END)
    parser.add_argument("--max-downloads", type=int, default=None)
    args = parser.parse_args()
    report = run_aggtrades_post_v9_pilot_collection_v9_19(
        Path("."),
        mode=args.mode,
        start_date=args.start_date,
        end_date=args.end_date,
        max_downloads=args.max_downloads,
    )
    summary = report["pilot_validation"]["summary"]
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "mode": report["mode"],
                "decision": report["v9_19_decision"]["decision"],
                "pilot_start": report["pilot_window"]["start"],
                "pilot_end": report["pilot_window"]["end"],
                "max_downloads": report["pilot_window"]["max_downloads"],
                "days_requested": summary["days_requested"],
                "days_attempted": summary["days_attempted"],
                "days_downloaded": summary["days_downloaded"],
                "days_normalized": summary["days_normalized"],
                "days_complete": summary["days_complete"],
                "days_failed": summary["days_failed"],
                "total_rows": summary["total_rows"],
                "raw_bytes_total": summary["raw_bytes_total"],
                "silver_bytes_total": summary["silver_bytes_total"],
                "runtime_seconds": summary["runtime_seconds"],
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
