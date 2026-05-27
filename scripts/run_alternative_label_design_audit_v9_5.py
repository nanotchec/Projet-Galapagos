from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.alternative_label_design_audit_v9_5 import run_alternative_label_design_audit_v9_5


def main() -> int:
    manifest = run_alternative_label_design_audit_v9_5(Path("."))
    summary = {
        "version": manifest["version"],
        "status": manifest["status"],
        "decision": manifest["v9_5_decision"]["decision"],
        "next_step": manifest["v9_5_decision"]["next_step"],
        "report": manifest["outputs"]["report_json"]["path"],
        "manifest": "reports/manifests/alternative_label_design_audit_v9_5_manifest.json",
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
