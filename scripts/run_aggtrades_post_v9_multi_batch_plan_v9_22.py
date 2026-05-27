from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_multi_batch_plan_v9_22 import (  # noqa: E402
    run_aggtrades_post_v9_multi_batch_plan_v9_22,
)


def main() -> int:
    report = run_aggtrades_post_v9_multi_batch_plan_v9_22(Path("."))
    coverage = report["current_coverage"]
    estimates = report["estimated_remaining_volume"]
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "mode": report["mode"],
                "decision": report["v9_22_decision"]["decision"],
                "current_coverage_start": coverage["current_coverage_start"],
                "current_coverage_end": coverage["current_coverage_end"],
                "days_covered": coverage["days_covered"],
                "days_remaining": coverage["days_remaining"],
                "gaps_detected": coverage["gaps_detected"],
                "proposed_batches_count": len(report["proposed_batches"]),
                "estimated_remaining_rows": estimates["estimated_remaining_rows"],
                "estimated_remaining_raw_bytes": estimates["estimated_remaining_raw_bytes"],
                "estimated_remaining_silver_bytes": estimates["estimated_remaining_silver_bytes"],
                "network_used": report["network_used"],
                "new_data_downloaded": report["new_data_downloaded"],
                "ingestion_executed": report["ingestion_executed"],
                "api_key_used": report["safety_flags"]["api_key_used"],
                "private_endpoint_used": report["safety_flags"]["private_endpoint_used"],
                "exchange_auth_used": report["safety_flags"]["exchange_auth_used"],
                "websocket_live_used": report["safety_flags"]["websocket_live_used"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
