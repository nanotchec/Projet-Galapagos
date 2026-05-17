from __future__ import annotations

import argparse

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default=str(project_path("data/paper/galapagos.sqlite")))
    args = parser.parse_args()
    store = SQLiteStore(args.database)
    for table in [
        "market_snapshots",
        "agent_decisions",
        "risk_decisions",
        "paper_trades",
        "positions",
        "performance_snapshots",
        "system_events",
    ]:
        count = store.query(f"SELECT COUNT(*) AS count FROM {table}")[0]["count"]
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()
