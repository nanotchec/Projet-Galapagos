from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_validation_v9_50 import run_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full-local", "audit-lite"], default="full-local")
    args = parser.parse_args()
    report = run_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50(mode=args.mode)
    print(
        json.dumps(
            {
                "version": report["version"],
                "mode": report["validation_mode"],
                "decision": report["decision"],
                "coverage_status": report["coverage_status"],
                "schema_status": report["schema_status"],
                "quality_status": report["quality_status"],
                "leakage_guard_status": report["leakage_guard_status"],
                "warnings": report["warnings"],
                "runtime_seconds": report["runtime_seconds"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
