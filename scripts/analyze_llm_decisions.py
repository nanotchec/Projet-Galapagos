from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.reports.llm_decisions_report import generate_llm_decisions_report
from galapagos.utils.paths import project_path


def main() -> None:
    paths = generate_llm_decisions_report(
        SQLiteStore(project_path("data/paper/galapagos.sqlite")),
        project_path("reports/diagnostics"),
    )
    print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))


if __name__ == "__main__":
    main()

