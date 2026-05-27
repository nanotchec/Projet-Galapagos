from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_batch_expansion_v9_21 import VERSION
from galapagos.data.aggtrades_post_v9_batch_expansion_v9_21_validation import (
    validate_aggtrades_post_v9_batch_expansion_v9_21,
)


def main() -> int:
    errors = validate_aggtrades_post_v9_batch_expansion_v9_21(Path("."))
    result = {"version": VERSION, "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
