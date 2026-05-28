from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.aggtrades_post_v9_resume_campaign_v9_25_1 import VERSION  # noqa: E402
from galapagos.data.aggtrades_post_v9_resume_campaign_v9_25_1_validation import validate_aggtrades_post_v9_resume_campaign_v9_25_1  # noqa: E402


def main() -> int:
    errors = validate_aggtrades_post_v9_resume_campaign_v9_25_1()
    payload = {"version": VERSION, "passed": not errors, "errors": errors}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
