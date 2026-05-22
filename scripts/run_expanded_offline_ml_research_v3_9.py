from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.expanded_window import run_expanded_offline_ml_research_v3_9


def main() -> None:
    manifest = run_expanded_offline_ml_research_v3_9(Path("."))
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "ml_run_id": manifest["ml_run_id"],
                "target_name": manifest["target_name"],
                "models": manifest["models"],
                "outputs": manifest["outputs"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
