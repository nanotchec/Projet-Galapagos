from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()

from galapagos.ml.robustness import run_multi_day_ml_robustness_v3_4


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-input-validation", action="store_true")
    args = parser.parse_args()
    validate_inputs = not args.skip_input_validation
    print("=== Generating Galapagos V3.4 Multi-Day ML Robustness & Falsification Audit ===")
    print(f"V3.4 run mode: validate_inputs={validate_inputs}")
    print("Historical V2.3 to V3.1 validations are not relaunched by this script.")
    manifest = run_multi_day_ml_robustness_v3_4(Path("."), validate_inputs=validate_inputs)
    print("Status:", manifest["status"])
    print("Robustness run id:", manifest["robustness_run_id"])
    print("Analyses:", ", ".join(manifest["analyses"].keys()))
    print("Warnings:", len(manifest["findings"]["warnings"]))
    print(json.dumps({"version": manifest["version"], "status": manifest["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
