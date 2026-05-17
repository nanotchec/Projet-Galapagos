from __future__ import annotations

import argparse

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.cycle import run_cycle
from galapagos.journal.sqlite_store import SQLiteStore
from galapagos.reports.daily_report import generate_daily_report, generate_daily_summary
from galapagos.utils.config_loader import load_profile, load_yaml
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="30m", choices=["30m", "4h"])
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    if args.summary:
        paths = generate_daily_summary(
            SQLiteStore(project_path("data/paper/galapagos.sqlite")),
            project_path("reports/daily"),
        )
        print(f"Markdown: {paths['markdown']}")
        print(f"JSON: {paths['json']}")
        return
    result = run_cycle(
        profile=load_profile(args.profile),
        risk_config=load_yaml("configs/risk.yaml"),
        llm_config=load_yaml("configs/llm.yaml"),
        database_path=str(project_path("data/paper/galapagos.sqlite")),
        use_mock_llm=True,
    )
    paths = generate_daily_report(result, project_path("reports/daily"))
    print(f"Markdown: {paths['markdown']}")
    print(f"JSON: {paths['json']}")


if __name__ == "__main__":
    main()
