from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.labels.refined_volatility_normalized_labels_v9_6 import run_refined_volatility_normalized_labels_v9_6


def main() -> int:
    manifest = run_refined_volatility_normalized_labels_v9_6(Path("."))
    summary = {
        "version": manifest.get("version"),
        "status": manifest.get("status"),
        "decision": manifest.get("decision"),
        "selected_volatility_threshold_multiplier": manifest.get("selected_volatility_threshold_multiplier"),
        "outputs": manifest.get("outputs", {}),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if manifest.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
