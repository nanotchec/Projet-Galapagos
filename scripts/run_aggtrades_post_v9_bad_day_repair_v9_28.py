from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_bad_day_repair_v9_28 import (  # noqa: E402
    run_aggtrades_post_v9_bad_day_repair_v9_28,
)


def main() -> int:
    report = run_aggtrades_post_v9_bad_day_repair_v9_28(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "decision": report["decision"],
                "bad_day": report["bad_day"],
                "duplicate_exact_count": report["duplicate_exact_count"],
                "duplicate_conflict_count": report["duplicate_conflict_count"],
                "repair_applied": report["repair_applied"],
                "tail_collection_executed": report["tail_collection_executed"],
                "local_file_coverage_start": report["local_file_coverage_start"],
                "local_file_coverage_end": report["local_file_coverage_end"],
                "complete_collection_reached": report["complete_collection_reached"],
                "future_full_coverage_complete": report["future_full_coverage_complete"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
