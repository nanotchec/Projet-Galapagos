from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.profile_comparison import generate_profile_comparison_report
from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.utils.paths import project_path


def main() -> None:
    store = SQLiteStore(project_path("data/paper/galapagos.sqlite"))
    paths = generate_profile_comparison_report(store, project_path("reports/diagnostics"))
    print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))


if __name__ == "__main__":
    main()

