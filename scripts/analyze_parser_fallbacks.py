from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.reports.parser_fallback_report import (  # noqa: E402
    analyze_parser_fallbacks,
    write_parser_fallback_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        default="reports/backtests/codex_setup_review_v1_8C_7.json",
    )
    args = parser.parse_args()
    report = Path(args.report)
    if not report.exists():
        raise RuntimeError(f"Setup review report not found: {report}")
    analysis = analyze_parser_fallbacks(report)
    md_path, json_path = write_parser_fallback_report(analysis)
    print(json.dumps({"markdown": str(md_path), "json": str(json_path), **analysis}, indent=2))


if __name__ == "__main__":
    main()
