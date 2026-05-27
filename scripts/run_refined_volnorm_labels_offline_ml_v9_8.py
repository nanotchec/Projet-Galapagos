from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.ml.refined_volnorm_labels_offline_ml_v9_8 import run_refined_volnorm_labels_offline_ml_v9_8


def main() -> int:
    manifest = run_refined_volnorm_labels_offline_ml_v9_8(Path("."))
    print(json.dumps({"version": manifest.get("version"), "status": manifest.get("status"), "decision": manifest.get("decision"), "outputs": manifest.get("outputs", {})}, indent=2, ensure_ascii=False))
    return 0 if manifest.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
