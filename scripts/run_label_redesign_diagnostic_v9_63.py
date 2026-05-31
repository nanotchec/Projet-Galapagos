from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.label_redesign_diagnostic_v9_63 import run_label_redesign_diagnostic_v9_63


def main() -> int:
    report = run_label_redesign_diagnostic_v9_63(Path("."))
    print(json.dumps({"version": report["version"], "decision": report["decision"], "status": report["status"]}, indent=2, ensure_ascii=False))
    return 0 if report["decision"].startswith("label_redesign_candidate_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
