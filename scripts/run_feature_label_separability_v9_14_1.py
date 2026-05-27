from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.feature_label_separability_v9_14_1 import run_feature_label_separability_v9_14_1


def main() -> int:
    report = run_feature_label_separability_v9_14_1(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "previous_v9_14_decision": report["previous_v9_14_decision"],
                "corrected_decision": report["corrected_decision"],
                "data_sources": len(report["data_source_inventory"]),
                "hypotheses": len(report["hypothesis_ranking"]),
                "no_backtest": report["safety_flags"]["no_backtest"],
                "no_walk_forward": report["safety_flags"]["no_walk_forward"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
