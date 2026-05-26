from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.features.ohlcv_trades_feature_audit import run_ohlcv_trades_feature_audit_v8_9


def main() -> None:
    manifest = run_ohlcv_trades_feature_audit_v8_9(Path("."))
    candidate = manifest["candidate_refined_feature_set"]
    print(
        json.dumps(
            {
                "version": manifest["version"],
                "status": manifest["status"],
                "window_start": manifest["input_dataset_manifest"]["window_start"],
                "window_end": manifest["input_dataset_manifest"]["window_end"],
                "total_days": manifest["input_dataset_manifest"]["total_days"],
                "original_feature_columns_count": manifest["input_dataset_manifest"]["feature_columns_count"],
                "selected_features_count": candidate["selected_features_count"],
                "dropped_features_count": candidate["dropped_features_count"],
                "review_features_count": candidate["review_features_count"],
                "manifest": "reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json",
                "report": "reports/features/ohlcv_trades_feature_audit_v8_9.json",
                "selection_report": "reports/features/ohlcv_trades_feature_selection_v8_9.json",
                "no_new_dataset": True,
                "no_ml_model": True,
                "no_backtest": True,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
