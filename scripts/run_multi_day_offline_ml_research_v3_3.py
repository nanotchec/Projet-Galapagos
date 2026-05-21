from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.multi_day import run_multi_day_offline_ml_research_v3_3


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-recent-layers", action="store_true")
    args = parser.parse_args()
    print("=== Generating Galapagos V3.3 Multi-Day Offline ML Research Baselines ===")
    print("V3.3 run mode: validate_dataset=True")
    print(f"V3.3 run mode: validate_recent_layers={args.validate_recent_layers}")
    print("Historical V2.3 to V2.8 validations are executed separately by audit commands.")
    manifest = run_multi_day_offline_ml_research_v3_3(
        Path("."),
        validate_dataset=True,
        validate_recent_layers=args.validate_recent_layers,
    )
    print("Status:", manifest["status"])
    print("ML run id:", manifest["ml_run_id"])
    for timeframe in ["1m", "5m", "15m", "1h"]:
        output = manifest["outputs"][timeframe]
        quality = manifest["quality"][timeframe]
        print(f"  {timeframe}: {output['path']} score_rows={output['rows']} used_rows={quality['rows_used_for_ml']}")
    print(json.dumps({"version": manifest["version"], "status": manifest["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
