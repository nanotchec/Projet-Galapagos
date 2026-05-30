from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_5y_full_coverage_validation_v9_32 import run_aggtrades_5y_full_coverage_validation_v9_32


def main() -> int:
    report = run_aggtrades_5y_full_coverage_validation_v9_32()
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "target_5y_window_start": report["target_5y_window_start"],
                "target_5y_window_end": report["target_5y_window_end"],
                "days_expected_5y": report["days_expected_5y"],
                "days_complete": report["days_complete"],
                "days_missing": report["days_missing"],
                "days_failed": report["days_failed"],
                "global_duplicate_count": report["global_duplicate_count"],
                "global_invalid_rows": report["global_invalid_rows"],
                "quality_status": report["quality_status"],
                "coverage_status": report["coverage_status"],
                "reporting_inconsistency_detected": report["reporting_inconsistency_detected"],
                "reporting_inconsistency_blocking": report["reporting_inconsistency_blocking"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
