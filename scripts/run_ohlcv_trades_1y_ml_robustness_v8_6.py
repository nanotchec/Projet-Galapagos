from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.ohlcv_trades_1y_robustness import run_ohlcv_trades_1y_ml_robustness_v8_6


def main() -> None:
    manifest = run_ohlcv_trades_1y_ml_robustness_v8_6(Path("."))
    print(
        json.dumps(
            {
                "version": manifest["version"],
                "status": manifest["status"],
                "robustness_run_id": manifest["robustness_run_id"],
                "window_start": manifest["input_ml_manifest"]["window_start"],
                "window_end": manifest["input_ml_manifest"]["window_end"],
                "total_days": manifest["input_ml_manifest"]["total_days"],
                "feature_columns_count": manifest["input_ml_manifest"]["feature_columns_count"],
                "analyses": sorted(manifest["analyses"]),
                "warnings_count": len(manifest["findings"]["warnings"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
