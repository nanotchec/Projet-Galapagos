from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47 import run_ohlcv_aggtrades_exact_5y_feature_store_v9_47


if __name__ == "__main__":
    report = run_ohlcv_aggtrades_exact_5y_feature_store_v9_47()
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "quality_status": report["quality_status"],
                "coverage_status": report["coverage_status"],
                "row_counts": report["row_counts"],
                "combined_feature_columns_count": report["combined_feature_columns_count"],
                "runtime_seconds": report["runtime_seconds"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
