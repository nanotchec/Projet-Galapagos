from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_full_coverage_validation_v9_29 import (  # noqa: E402
    run_aggtrades_post_v9_full_coverage_validation_v9_29,
)


def main() -> int:
    report = run_aggtrades_post_v9_full_coverage_validation_v9_29()
    summary = {
        "version": report["version"],
        "decision": report["decision"],
        "days_expected": report["days_expected"],
        "days_complete": report["days_complete"],
        "days_missing": report["days_missing"],
        "days_failed": report["days_failed"],
        "global_duplicate_count": report["global_duplicate_count"],
        "global_invalid_rows": report["global_invalid_rows"],
        "quality_status": report["quality_status"],
        "complete_collection_reached": report["complete_collection_reached"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
