from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.feature_label_separability_v9_14 import run_feature_label_separability_v9_14


def main() -> int:
    report = run_feature_label_separability_v9_14(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "decision": report["v9_14_decision"]["decision"],
                "target_name": report["target_name"],
                "full_data_available": report["full_data_available"],
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
