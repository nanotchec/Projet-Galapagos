from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.aggtrades_exact_5y_feature_enrichment_v9_45 import run_aggtrades_exact_5y_feature_enrichment_v9_45


if __name__ == "__main__":
    report = run_aggtrades_exact_5y_feature_enrichment_v9_45()
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "quality_status": report["quality_status"],
                "coverage_status": report["coverage_status"],
                "row_counts": report["row_counts"],
                "runtime_seconds": report["runtime_seconds"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
