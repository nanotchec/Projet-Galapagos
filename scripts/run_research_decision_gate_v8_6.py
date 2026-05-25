from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.ohlcv_trades_1y_robustness import run_research_decision_gate_v8_6
from galapagos.ml.ohlcv_trades_1y_robustness_validation import validate_ohlcv_trades_1y_ml_robustness_v8_6


def main() -> None:
    validation = validate_ohlcv_trades_1y_ml_robustness_v8_6(Path("."))
    if not validation["passed"]:
        raise RuntimeError(f"V8.6 robustness validation failed before decision gate: {validation['errors']}")
    decision = run_research_decision_gate_v8_6(Path("."))
    print(
        json.dumps(
            {
                "version": decision["version"],
                "status": decision["status"],
                "decision_gate_type": decision["decision_gate_type"],
                "summary_verdict": decision["summary_verdict"],
                "recommended_next_step": decision["recommended_next_step"],
                "secondary_next_step": decision["secondary_next_step"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
