from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.reports.llm_offline_decision_report import (
    analyze_llm_offline_decisions,
    write_llm_offline_decision_report,
)
from galapagos.utils.paths import project_path


def main() -> None:
    suite_path = project_path("reports/backtests/llm_offline_suite_v1_7.json")
    payload = json.loads(Path(suite_path).read_text(encoding="utf-8"))
    results = [
        {"policy": result["policy"], "raw_results": {result["profile"]: result}}
        for result in payload.get("results", [])
    ]
    analysis = analyze_llm_offline_decisions(results)
    paths = write_llm_offline_decision_report(analysis, project_path("reports/diagnostics"))
    print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))


if __name__ == "__main__":
    main()
