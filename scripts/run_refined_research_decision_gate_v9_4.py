from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.refined_research_decision_gate_v9_4 import run_refined_research_decision_gate_v9_4


def main() -> int:
    manifest = run_refined_research_decision_gate_v9_4(Path("."))
    print(
        json.dumps(
            {
                "version": manifest["version"],
                "status": manifest["status"],
                "research_decision": manifest["research_decision"],
                "manifest": "reports/manifests/refined_research_decision_gate_v9_4_manifest.json",
                "decision_report": "reports/research_decisions/refined_research_decision_gate_v9_4.json",
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
