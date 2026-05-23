from __future__ import annotations

import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.datasets.one_year_window import run_one_year_offline_supervised_dataset_v4_5


def main() -> None:
    manifest = run_one_year_offline_supervised_dataset_v4_5(Path("."))
    print(json.dumps({"status": manifest["status"], "dataset_run_id": manifest["dataset_run_id"], "outputs": manifest["outputs"]}, indent=2))


if __name__ == "__main__":
    main()
