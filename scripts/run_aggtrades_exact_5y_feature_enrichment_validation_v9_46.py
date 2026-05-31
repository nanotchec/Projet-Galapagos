from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.aggtrades_exact_5y_feature_enrichment_validation_v9_46 import run_aggtrades_exact_5y_feature_enrichment_validation_v9_46


if __name__ == "__main__":
    report = run_aggtrades_exact_5y_feature_enrichment_validation_v9_46()
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "validation_mode": report["validation_mode"],
                "quality_status": report["quality_status"],
                "coverage_status": report["coverage_status"],
                "row_counts": report["row_counts"],
                "runtime_seconds": report["runtime_seconds"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
