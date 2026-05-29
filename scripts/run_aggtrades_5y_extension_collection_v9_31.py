from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_5y_extension_collection_v9_31 import run_aggtrades_5y_extension_collection_v9_31  # noqa: E402


def main() -> int:
    report = run_aggtrades_5y_extension_collection_v9_31()
    summary = {
        "version": report["version"],
        "decision": report["decision"],
        "extension_window_start": report["extension_window_start"],
        "extension_window_end": report["extension_window_end"],
        "batches_planned": report["batches_planned"],
        "batches_executed": report["batches_executed"],
        "batches_complete": report["batches_complete"],
        "batches_failed": report["batches_failed"],
        "days_downloaded": report["days_downloaded"],
        "days_normalized": report["days_normalized"],
        "days_complete": report["days_complete"],
        "days_missing": report["days_missing"],
        "days_failed": report["days_failed"],
        "days_quarantined": report["days_quarantined"],
        "total_rows_new": report["total_rows_new"],
        "raw_bytes_new": report["raw_bytes_new"],
        "silver_bytes_new": report["silver_bytes_new"],
        "local_file_coverage_start": report["local_file_coverage_start"],
        "local_file_coverage_end": report["local_file_coverage_end"],
        "complete_extension_reached": report["complete_extension_reached"],
        "target_5y_collection_reached": report["target_5y_collection_reached"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if report["decision"] == "aggtrades_5y_extension_collection_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
