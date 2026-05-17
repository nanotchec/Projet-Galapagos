from __future__ import annotations

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.cycle import run_cycle
from galapagos.reports.daily_report import generate_daily_report
from galapagos.utils.config_loader import load_profile, load_yaml
from galapagos.utils.paths import project_path


def main() -> None:
    for profile_name in ["30m", "4h"]:
        result = run_cycle(
            profile=load_profile(profile_name),
            risk_config=load_yaml("configs/risk.yaml"),
            llm_config=load_yaml("configs/llm.yaml"),
            database_path=str(project_path("data/paper/galapagos.sqlite")),
            use_mock_llm=True,
        )
        paths = generate_daily_report(result, project_path("reports/daily"))
        print(f"Generated {paths['markdown']}")


if __name__ == "__main__":
    main()
