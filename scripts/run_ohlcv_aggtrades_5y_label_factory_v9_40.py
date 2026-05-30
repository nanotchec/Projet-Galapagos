from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40 import run_ohlcv_aggtrades_5y_label_factory_v9_40


def main() -> int:
    report = run_ohlcv_aggtrades_5y_label_factory_v9_40()
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "labels_created": report["labels_created"],
                "dataset_created": report["dataset_created"],
                "selected_primary_label": report["selected_primary_label"],
                "row_counts": report["row_counts"],
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
