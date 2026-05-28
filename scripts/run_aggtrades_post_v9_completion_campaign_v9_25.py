from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import (  # noqa: E402
    run_aggtrades_post_v9_completion_campaign_v9_25,
)


def main() -> int:
    report = run_aggtrades_post_v9_completion_campaign_v9_25()
    summary = report["campaign_summary"]
    result = {
        "version": report["version"],
        "status": report["status"],
        "decision": report["decision"],
        "campaign_start": summary["campaign_start"],
        "campaign_end": summary["campaign_end"],
        "batches_planned": summary["batches_planned"],
        "batches_executed": summary["batches_executed"],
        "batches_complete": summary["batches_complete"],
        "batches_failed": summary["batches_failed"],
        "days_requested_total": summary["days_requested_total"],
        "days_attempted_total": summary["days_attempted_total"],
        "days_downloaded_total": summary["days_downloaded_total"],
        "days_normalized_total": summary["days_normalized_total"],
        "days_complete_total": summary["days_complete_total"],
        "days_failed_total": summary["days_failed_total"],
        "days_quarantined_total": summary["days_quarantined_total"],
        "days_skipped_existing_total": summary["days_skipped_existing_total"],
        "total_rows_new": summary["total_rows_new"],
        "total_rows_cumulative": summary["total_rows_cumulative"],
        "raw_bytes_new": summary["raw_bytes_new"],
        "silver_bytes_new": summary["silver_bytes_new"],
        "raw_bytes_cumulative": summary["raw_bytes_cumulative"],
        "silver_bytes_cumulative": summary["silver_bytes_cumulative"],
        "runtime_seconds_total": summary["runtime_seconds_total"],
        "local_file_coverage_start": summary["local_file_coverage_start"],
        "local_file_coverage_end": summary["local_file_coverage_end"],
        "reported_cumulative_coverage_start": summary["reported_cumulative_coverage_start"],
        "reported_cumulative_coverage_end": summary["reported_cumulative_coverage_end"],
        "complete_collection_reached": summary["complete_collection_reached"],
        "future_full_coverage_complete": summary["future_full_coverage_complete"],
        "network_used": report["network_used"],
        "api_key_used": report["safety_flags"]["api_key_used"],
        "private_endpoint_used": report["safety_flags"]["private_endpoint_used"],
        "exchange_auth_used": report["safety_flags"]["exchange_auth_used"],
        "websocket_live_used": report["safety_flags"]["websocket_live_used"],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
