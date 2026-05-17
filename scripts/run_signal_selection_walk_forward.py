from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.signal_selection.report_models import write_selection_report
from galapagos.research.signal_selection.selection_rules import build_default_rules
from galapagos.research.signal_selection.walk_forward_validation import (
    run_walk_forward_validation,
)
from galapagos.utils.version import display_version, normalize_version


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V1.24.1 signal selection walk-forward")
    parser.add_argument("--features-report", required=True)
    parser.add_argument("--filter-sweep-report", required=True)
    parser.add_argument("--version", default="v1.24.1")
    parser.add_argument("--iterations", type=int, default=500)
    args = parser.parse_args()

    version = normalize_version(args.version)
    display = display_version(version)
    features_payload = _read_json(Path(args.features_report))
    sweep_payload = _read_json(Path(args.filter_sweep_report))
    features = pd.DataFrame(
        features_payload.get("feature_rows")
        or features_payload.get("rows_all")
        or features_payload.get("feature_sample", [])
    )
    if features.empty:
        payload = {
            "version": display,
            "status": "missing_features",
            "rows": [],
            "walk_forward_verdict": "WALK_FORWARD_SAMPLE_TOO_SMALL",
            "codex_cli_called": False,
            "holdout_executed": False,
            "no_real_trading": True,
        }
    else:
        top_rule_names = _top_causal_rule_names(sweep_payload)
        payload = {
            "version": display,
            "status": "completed",
            **run_walk_forward_validation(
                features,
                rules=build_default_rules(),
                top_rule_names=top_rule_names,
                iterations=args.iterations,
            ),
            "codex_cli_called": False,
            "holdout_executed": False,
            "no_real_trading": True,
        }
    write_selection_report(
        stem="signal_selection_walk_forward",
        version=version,
        payload=payload,
        title="Signal Selection Walk-Forward",
        lines=[
            f"Verdict walk-forward: {payload['walk_forward_verdict']}.",
            f"Fenêtres: {payload.get('windows', [])}.",
            "Le filtre est analyse offline uniquement; il n'est pas active en trading.",
            "Aucun Codex CLI, aucun holdout, aucun ordre reel.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _top_causal_rule_names(sweep_payload: dict[str, Any]) -> list[str]:
    rows = [
        row
        for row in sweep_payload.get("rows", [])
        if row.get("causal", True) and row.get("rule_name") != "no_trade"
    ]
    rows = sorted(
        rows,
        key=lambda row: (
            row.get("beats_random_p95", False),
            row.get("net_mean_pnl_pct", -999.0),
            row.get("selected_count", 0),
        ),
        reverse=True,
    )
    names = ["low_frequency_strict_score"]
    for row in rows:
        name = row.get("rule_name")
        if name and name not in names:
            names.append(name)
        if len(names) >= 3:
            break
    return names


if __name__ == "__main__":
    main()
