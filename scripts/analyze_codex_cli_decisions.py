from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.reports.codex_cli_report import write_codex_cli_decision_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="reports/backtests/codex_cli_sample_backtest_v1_8C_1.json",
    )
    args = parser.parse_args()
    path = Path(args.input)
    if not path.exists() and args.input.endswith("v1_8C_1.json"):
        path = Path("reports/backtests/codex_cli_sample_backtest_v1_8C.json")
    if not path.exists():
        raise RuntimeError(f"Codex CLI sample report not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    total = int(payload.get("total_codex_cli_calls") or 0)
    no_trade = int((payload.get("decision_distribution") or {}).get("NO_TRADE", 0))
    active = sum(
        int((payload.get("decision_distribution") or {}).get(key, 0))
        for key in ["LONG", "SHORT", "CLOSE"]
    )
    analysis = {
        **payload,
        "valid_json_rate": (payload.get("valid_json_count", 0) / total if total else 0.0),
        "active_decision_rate": active / total if total else 0.0,
        "no_trade_rate": no_trade / total if total else 0.0,
    }
    paths = write_codex_cli_decision_report(analysis, Path("reports/diagnostics"))
    print(json.dumps(paths, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
