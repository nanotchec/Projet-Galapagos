from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.refined_volnorm_research_decision_gate_v9_10 import run_refined_volnorm_research_decision_gate_v9_10


def main() -> int:
    report = run_refined_volnorm_research_decision_gate_v9_10(Path("."))
    print(json.dumps({"version": report.get("version"), "status": report.get("status"), "research_decision": report.get("research_decision")}, indent=2, ensure_ascii=False))
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
