from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.ml.refined_volnorm_strict_walk_forward_v9_9_validation import validate_refined_volnorm_strict_walk_forward_v9_9


def main() -> int:
    result = validate_refined_volnorm_strict_walk_forward_v9_9(Path("."))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
