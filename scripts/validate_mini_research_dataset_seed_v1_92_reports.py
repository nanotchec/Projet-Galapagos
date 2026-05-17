from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import argparse

from galapagos.research.mini_research_dataset_seed.validator import validate_report_set


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1_92")
    args = parser.parse_args()
    if args.version != "v1_92":
        raise SystemExit(f"Unsupported version: {args.version}")
    errors = validate_report_set(PROJECT_ROOT, version_suffix="v1_92")
    if errors:
        print("FAIL: V1.92 validation failed")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("PASS: V1.92 mini research dataset seed reports validated.")


if __name__ == "__main__":
    main()
