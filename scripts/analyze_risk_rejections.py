from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.risk_rejection_analysis import analyze_risk_rejections
from galapagos.utils.paths import project_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-json", action="append", default=[])
    parser.add_argument("--latest", type=int, default=10)
    args = parser.parse_args()

    files = [Path(path) for path in args.run_json] or _latest_backtests(args.latest)
    results = [json.loads(path.read_text(encoding="utf-8")) for path in files]
    analysis = analyze_risk_rejections(results)
    generated_at = datetime.now(UTC).isoformat()
    name = generated_at[:10]
    output_dir = project_path("reports/diagnostics")
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": generated_at,
        "source_files": [str(path) for path in files],
        **analysis,
    }
    json_path = output_dir / f"risk_rejections_{name}.json"
    md_path = output_dir / f"risk_rejections_{name}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "markdown": str(md_path),
                "json": str(json_path),
                "total_rejections": analysis["total_rejections"],
                "top_10_reasons": analysis["top_10_reasons"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def _latest_backtests(limit: int) -> list[Path]:
    directory = project_path("reports/backtests")
    files = sorted(directory.glob("backtest_*.json"), key=lambda path: path.stat().st_mtime)
    return files[-limit:]


def _markdown(payload: dict) -> str:
    lines = [
        f"# Analyse des refus risk engine - {payload['generated_at_utc'][:10]}",
        "",
        f"- Genere le: {payload['generated_at_utc']}",
        f"- Nombre total de refus: {payload['total_rejections']}",
        "",
        "## Refus par profil",
    ]
    for key, value in payload["rejections_by_profile"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Refus par strategie"])
    for key, value in payload["rejections_by_strategy"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Top raisons"])
    for reason, count in payload["top_10_reasons"]:
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Exemples"])
    for example in payload["examples"]:
        lines.append(
            f"- {example['timestamp']} | {example['profile']} | "
            f"{example['decision']} | {example['strategy']} | {example['reasons']}"
        )
    lines.extend(["", "## Recommandations"])
    for recommendation in payload["recommendations"]:
        lines.append(f"- {recommendation}")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
