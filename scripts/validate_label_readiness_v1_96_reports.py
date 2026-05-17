from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
for path in (PROJECT_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from galapagos.research.label_readiness.validator import validate_report_set  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1_96")
    args = parser.parse_args()
    if args.version != "v1_96":
        raise SystemExit(f"Unsupported version: {args.version}")
    errors = validate_report_set(PROJECT_ROOT, version_suffix="v1_96")
    if errors:
        print("FAIL: V1.96 validation failed")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print("PASS: V1.96 label readiness reports validated.")


if __name__ == "__main__":
    main()

