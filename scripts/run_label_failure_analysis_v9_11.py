from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.label_failure_analysis_v9_11 import run_label_failure_analysis_v9_11


def main() -> int:
    report = run_label_failure_analysis_v9_11(Path("."))
    print(json.dumps({"version": report["version"], "status": report["status"], "decision": report["v9_11_decision"]["decision"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
