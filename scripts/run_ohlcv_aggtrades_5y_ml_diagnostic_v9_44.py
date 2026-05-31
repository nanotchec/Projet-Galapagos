from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.ohlcv_aggtrades_5y_ml_diagnostic_v9_44 import run_ml_diagnostic_v9_44


if __name__ == "__main__":
    report = run_ml_diagnostic_v9_44()
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "next_recommendation": report["next_recommendation"],
                "baseline_clear_wins_count": report["ml_result_summary"]["baseline_clear_wins_count"],
                "no_clear_edge_vs_shuffled_labels_count": report["ml_result_summary"]["no_clear_edge_vs_shuffled_labels_count"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
