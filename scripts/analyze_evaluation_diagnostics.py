from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.analysis.evaluation_diagnostics import analyze_evaluation_diagnostics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-calibration", action="store_true")
    parser.add_argument("--include-validation", action="store_true")
    parser.add_argument("--calibration-dir", default=None)
    parser.add_argument("--validation-dir", default=None)
    args = parser.parse_args()
    include_calibration = args.include_calibration or not args.include_validation
    include_validation = args.include_validation or not args.include_calibration
    analysis = analyze_evaluation_diagnostics(
        include_calibration=include_calibration,
        include_validation=include_validation,
        calibration_dir=args.calibration_dir,
        validation_dir=args.validation_dir,
    )
    output = Path("reports/evaluation")
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "evaluation_diagnostics_v1_9C.json"
    md_path = output / "evaluation_diagnostics_v1_9C.md"
    json_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(analysis), encoding="utf-8")
    print(json.dumps({"markdown": str(md_path), "json": str(json_path), **analysis}, indent=2))


def _markdown(analysis: dict) -> str:
    lines = [
        "# Diagnostics evaluation Galapagos V1.9C",
        "",
        (
            "Analyse offline des ledgers calibration + validation. "
            "Aucun appel Codex CLI, aucun holdout."
        ),
        "",
        f"- Verdict : {analysis['verdict']}",
        f"- Holdout execute : {analysis['holdout_executed']}",
        "",
        "## Resume global",
        "",
        json.dumps(analysis["global"]["trades"], indent=2, ensure_ascii=False),
        "",
        "## Couts",
        "",
        json.dumps(analysis["global"]["costs"], indent=2, ensure_ascii=False),
        "",
        "## Side LONG/SHORT",
        "",
        json.dumps(analysis["global"]["side"], indent=2, ensure_ascii=False),
        "",
        "## Regimes",
        "",
        json.dumps(analysis["global"]["regime"], indent=2, ensure_ascii=False),
        "",
        "## Setup quality / score / confidence",
        "",
        json.dumps(analysis["global"]["setup_quality"], indent=2, ensure_ascii=False),
        "",
        "## Exit reasons",
        "",
        json.dumps(analysis["global"]["exit_reason"], indent=2, ensure_ascii=False),
        "",
        "## Filtres hypothetiques",
        "",
        json.dumps(analysis["hypothetical_filters"], indent=2, ensure_ascii=False),
        "",
        "## Reponses",
        "",
        json.dumps(analysis["answers"], indent=2, ensure_ascii=False),
        "",
        "## Fenetres",
    ]
    for window in analysis["windows"]:
        lines.extend(
            [
                f"### {window['window']}",
                "",
                f"- Candidats : {window['candidates_submitted']}",
                f"- Decisions : {window['decision_distribution']}",
                f"- Parse success : {window['parse_success']}",
                f"- Risk rejects : {window['risk_rejects']}",
                f"- Ledger matches official : {window['ledger_pnl_matches_official']}",
                f"- Trades : {window['trades']}",
                f"- Couts : {window['costs']}",
                "",
            ]
        )
    lines.extend(["", analysis["safety"]])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
