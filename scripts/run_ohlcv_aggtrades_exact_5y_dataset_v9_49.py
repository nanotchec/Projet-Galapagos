from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.ohlcv_aggtrades_exact_5y_dataset_v9_49 import run_ohlcv_aggtrades_exact_5y_dataset_v9_49


def main() -> int:
    report = run_ohlcv_aggtrades_exact_5y_dataset_v9_49()
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "dataset_created": report["dataset_created"],
                "target_name": report["target_name"],
                "row_counts": report["row_counts"],
                "valid_row_counts": report["valid_row_counts"],
                "invalid_row_counts": report["invalid_row_counts"],
                "leakage_guard": report["leakage_guard"]["status"],
                "quality_status": report["quality_status"],
                "coverage_status": report["coverage_status"],
                "runtime_seconds": report["runtime_seconds"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
