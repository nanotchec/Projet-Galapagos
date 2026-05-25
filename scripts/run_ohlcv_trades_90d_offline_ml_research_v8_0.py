from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.ohlcv_trades_90d_window import run_ohlcv_trades_90d_offline_ml_research_v8_0


def main() -> None:
    manifest = run_ohlcv_trades_90d_offline_ml_research_v8_0(Path("."))
    summary = {
        "version": manifest["version"],
        "status": manifest["status"],
        "ml_run_id": manifest["ml_run_id"],
        "window_start": manifest["input_dataset_manifest"]["window_start"],
        "window_end": manifest["input_dataset_manifest"]["window_end"],
        "total_days": manifest["input_dataset_manifest"]["total_days"],
        "feature_columns_count": manifest["feature_columns_count"],
        "outputs": manifest["outputs"],
        "models": manifest["models"],
        "target_name": manifest["target_name"],
        "comparison_to_references": {
            name: payload["status"] for name, payload in manifest["comparison_to_references"].items()
        },
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
