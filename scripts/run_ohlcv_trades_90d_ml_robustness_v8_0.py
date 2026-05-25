from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.ohlcv_trades_90d_robustness import run_ohlcv_trades_90d_ml_robustness_v8_0


def main() -> None:
    manifest = run_ohlcv_trades_90d_ml_robustness_v8_0(Path("."))
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "robustness_run_id": manifest["robustness_run_id"],
                "window_start": manifest["input_ml_manifest"]["window_start"],
                "window_end": manifest["input_ml_manifest"]["window_end"],
                "total_days": manifest["input_ml_manifest"]["total_days"],
                "analyses": sorted(manifest["analyses"]),
                "warnings": len(manifest["findings"]["warnings"]),
                "findings": {
                    "robust_edge_claimed": manifest["findings"]["robust_edge_claimed"],
                    "strategy_validated": manifest["findings"]["strategy_validated"],
                    "backtest_performed": manifest["findings"]["backtest_performed"],
                    "actionable_signal_produced": manifest["findings"]["actionable_signal_produced"],
                    "ohlcv_trades_validated_for_trading": manifest["findings"]["ohlcv_trades_validated_for_trading"],
                },
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
