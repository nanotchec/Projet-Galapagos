from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_resume_campaign_v9_25_1 import run_aggtrades_post_v9_resume_campaign_v9_25_1  # noqa: E402


def main() -> int:
    report = run_aggtrades_post_v9_resume_campaign_v9_25_1()
    summary = report["resume_summary"]
    payload = {
        "version": report["version"],
        "status": report["status"],
        "decision": report["decision"],
        "first_missing_day_before_resume": report["first_missing_day_before_resume"],
        "free_bytes_current": report["disk_preflight"]["free_bytes_current"],
        "safe_to_continue_now": report["disk_preflight"]["safe_to_continue_now"],
        "batches_planned": summary["batches_planned"],
        "batches_executed": summary["batches_executed"],
        "batches_complete": summary["batches_complete"],
        "batches_failed": summary["batches_failed"],
        "days_downloaded_total": summary["days_downloaded_total"],
        "days_normalized_total": summary["days_normalized_total"],
        "days_complete_total": summary["days_complete_total"],
        "days_failed_total": summary["days_failed_total"],
        "days_quarantined_total": summary["days_quarantined_total"],
        "days_skipped_existing_total": summary["days_skipped_existing_total"],
        "total_rows_new": summary["total_rows_new"],
        "raw_bytes_new": summary["raw_bytes_new"],
        "silver_bytes_new": summary["silver_bytes_new"],
        "local_file_coverage_start": summary["local_file_coverage_start"],
        "local_file_coverage_end": summary["local_file_coverage_end"],
        "complete_collection_reached": summary["complete_collection_reached"],
        "future_full_coverage_complete": summary["future_full_coverage_complete"],
        "network_used": report["safety_flags"]["network_used"],
        "api_key_used": report["safety_flags"]["api_key_used"],
        "private_endpoint_used": report["safety_flags"]["private_endpoint_used"],
        "exchange_auth_used": report["safety_flags"]["exchange_auth_used"],
        "websocket_live_used": report["safety_flags"]["websocket_live_used"],
        "no_data_deletion": report["safety_flags"]["no_data_deletion"],
        "no_destructive_cleanup": report["safety_flags"]["no_destructive_cleanup"],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
