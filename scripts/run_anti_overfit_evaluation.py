from __future__ import annotations

import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.evaluation.anti_overfit_runner import run_anti_overfit_evaluation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--mode",
        choices=["dry-run", "calibration", "validation", "holdout", "all"],
        default="dry-run",
    )
    parser.add_argument("--allow-codex-cli", action="store_true")
    parser.add_argument("--use-decision-cache", action="store_true")
    parser.add_argument("--cache-readonly", action="store_true")
    parser.add_argument("--cache-write", action="store_true")
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()

    result = run_anti_overfit_evaluation(
        config_path=args.config,
        mode=args.mode,
        allow_codex_cli=args.allow_codex_cli,
        cache_options={
            "use_decision_cache": args.use_decision_cache,
            "cache_readonly": args.cache_readonly,
            "cache_write": args.cache_write,
            "refresh_cache": args.refresh_cache,
        },
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
