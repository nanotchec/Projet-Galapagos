from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.funding_tail_resolution_v9_56_validation import validate_funding_tail_resolution_file_v9_56


def main() -> int:
    result = validate_funding_tail_resolution_file_v9_56(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
