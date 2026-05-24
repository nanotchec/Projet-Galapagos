from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.one_year_robustness import run_one_year_ml_robustness_v4_7


def main() -> None:
    manifest = run_one_year_ml_robustness_v4_7(Path("."))
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "robustness_run_id": manifest["robustness_run_id"],
                "analyses": sorted(manifest["analyses"]),
                "warnings": len(manifest["findings"]["warnings"]),
                "findings": {
                    "robust_edge_claimed": manifest["findings"]["robust_edge_claimed"],
                    "strategy_validated": manifest["findings"]["strategy_validated"],
                    "backtest_performed": manifest["findings"]["backtest_performed"],
                    "actionable_signal_produced": manifest["findings"]["actionable_signal_produced"],
                },
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
