from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.max_history_window import run_max_history_offline_ml_research_v5_4


def main() -> None:
    manifest = run_max_history_offline_ml_research_v5_4(Path("."))
    summary = {
        "version": manifest["version"],
        "status": manifest["status"],
        "ml_run_id": manifest["ml_run_id"],
        "window_start": manifest["input_dataset_manifest"]["window_start"],
        "window_end": manifest["input_dataset_manifest"]["window_end"],
        "total_days": manifest["input_dataset_manifest"]["total_days"],
        "outputs": manifest["outputs"],
        "models": manifest["models"],
        "target_name": manifest["target_name"],
        "audit_lite_does_not_replace_full_validation": True,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
