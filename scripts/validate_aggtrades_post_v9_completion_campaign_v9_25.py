from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import VERSION  # noqa: E402
from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25_validation import (  # noqa: E402
    validate_aggtrades_post_v9_completion_campaign_v9_25,
)


def main() -> int:
    errors = validate_aggtrades_post_v9_completion_campaign_v9_25(Path("."))
    result = {"version": VERSION, "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
