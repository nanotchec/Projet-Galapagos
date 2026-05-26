from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.strict_walk_forward import run_strict_walk_forward_validation_v8_7


def main() -> None:
    manifest = run_strict_walk_forward_validation_v8_7(Path("."))
    print(
        json.dumps(
            {
                "version": manifest["version"],
                "status": manifest["status"],
                "window_start": manifest["input_dataset_manifest"]["window_start"],
                "window_end": manifest["input_dataset_manifest"]["window_end"],
                "total_days": manifest["input_dataset_manifest"]["total_days"],
                "feature_columns_count": manifest["feature_columns_count"],
                "folds_count": {timeframe: len(folds) for timeframe, folds in manifest["folds"].items()},
                "score_rows": {timeframe: payload["rows"] for timeframe, payload in manifest["outputs"]["scores"].items()},
                "warnings": len(manifest["findings"]["warnings"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if manifest["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
