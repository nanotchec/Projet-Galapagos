from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.redesigned_5y_label_factory_v9_64 import run_redesigned_5y_label_factory_v9_64


def main() -> int:
    report = run_redesigned_5y_label_factory_v9_64(Path("."))
    print(json.dumps({"version": report["version"], "decision": report["decision"], "status": report["status"]}, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
