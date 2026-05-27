from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.derivatives_data_extension_readiness_v9_15 import run_derivatives_data_extension_readiness_v9_15


def main() -> int:
    report = run_derivatives_data_extension_readiness_v9_15(Path("."))
    print(
        json.dumps(
            {
                "version": report["version"],
                "status": report["status"],
                "decision": report["v9_15_decision"]["decision"],
                "features_candidate_created": report["features_candidate_created"],
                "funding_readiness": report["funding_readiness"]["readiness_decision"],
                "open_interest_readiness": report["open_interest_readiness"]["readiness_decision"],
                "network_used": report["safety_flags"]["network_used"],
                "no_new_data_download": report["safety_flags"]["no_new_data_download"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
