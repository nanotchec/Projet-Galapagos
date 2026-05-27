from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.datasets.h4_label_candidate_dataset_v9_13 import run_h4_label_candidate_dataset_v9_13


def main() -> int:
    report = run_h4_label_candidate_dataset_v9_13(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "decision": report["decision"],
                "target_name": report.get("target_name"),
                "outputs": {timeframe: output["rows"] for timeframe, output in report.get("outputs", {}).items()},
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
