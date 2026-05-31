from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.derivatives_funding_oi_feature_store_v9_54 import run_derivatives_funding_oi_feature_store_v9_54


def main() -> int:
    report = run_derivatives_funding_oi_feature_store_v9_54(Path("."))
    print(json.dumps({"version": report["version"], "decision": report["decision"], "status": report["status"]}, indent=2, ensure_ascii=False))
    return 0 if report["feature_store_created"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
