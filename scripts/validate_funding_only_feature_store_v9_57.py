from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.features.funding_only_feature_store_v9_57_validation import validate_funding_only_feature_store_file_v9_57


def main() -> int:
    result = validate_funding_only_feature_store_file_v9_57(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
