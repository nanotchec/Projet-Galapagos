from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.datasets.expanded_window import run_expanded_offline_supervised_dataset_v3_8


def main() -> None:
    manifest = run_expanded_offline_supervised_dataset_v3_8(Path("."))
    print(json.dumps({"status": manifest["status"], "dataset_run_id": manifest["dataset_run_id"], "outputs": manifest["outputs"]}, indent=2))


if __name__ == "__main__":
    main()
