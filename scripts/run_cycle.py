from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.cycle import run_cycle
from galapagos.utils.config_loader import load_profile, load_yaml
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        default="30m",
        choices=["30m", "4h", "galapagos_30m", "galapagos_4h"],
    )
    parser.add_argument("--real-data", action="store_true")
    parser.add_argument("--openai-codex", action="store_true")
    parser.add_argument(
        "--mock-decision",
        default="NO_TRADE",
        choices=["NO_TRADE", "LONG", "SHORT", "CLOSE", "HOLD"],
    )
    parser.add_argument("--database", default=str(project_path("data/paper/galapagos.sqlite")))
    args = parser.parse_args()

    result = run_cycle(
        profile=load_profile(args.profile),
        risk_config=load_yaml("configs/risk.yaml"),
        llm_config=load_yaml("configs/llm.yaml"),
        database_path=args.database,
        use_real_data=args.real_data,
        use_mock_llm=not args.openai_codex,
        mock_decision=args.mock_decision,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
