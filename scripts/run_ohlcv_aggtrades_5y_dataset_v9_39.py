from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_39 import run_ohlcv_aggtrades_5y_dataset_v9_39


def main() -> int:
    report = run_ohlcv_aggtrades_5y_dataset_v9_39(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "dataset_created": report["dataset_created"],
                "target_name": report["target_name"],
                "label_readiness_status": report["label_readiness"]["status"],
                "quality_status": report["quality_status"],
                "coverage_status": report["coverage_status"],
                "runtime_seconds": report["runtime_seconds"],
                "status": report["status"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
