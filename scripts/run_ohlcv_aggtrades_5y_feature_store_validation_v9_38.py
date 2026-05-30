from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.ohlcv_aggtrades_5y_feature_store_validation_v9_38 import run_ohlcv_aggtrades_5y_feature_store_validation_v9_38


def main() -> int:
    report = run_ohlcv_aggtrades_5y_feature_store_validation_v9_38(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "timeframes": report["timeframes"],
                "actual_rows": report["actual_rows"],
                "feature_columns_count": report["feature_columns_count"],
                "quality_status": report["quality_status"],
                "coverage_status": report["coverage_status"],
                "schema_status": report["schema_status"],
                "leakage_guard_status": report["leakage_guard_status"],
                "runtime_seconds": report["runtime_seconds"],
                "status": report["status"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
