from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.signal_selection.leakage_audit import audit_signal_selection_leakage
from galapagos.research.signal_selection.report_models import write_selection_report
from galapagos.research.signal_selection.selection_rules import build_default_rules
from galapagos.utils.version import display_version, normalize_version


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit signal selection leakage risk")
    parser.add_argument("--version", default="v1.24.1")
    args = parser.parse_args()
    version = normalize_version(args.version)
    display = display_version(version)
    source_paths = [
        "src/galapagos/research/signal_selection/candidate_features.py",
        "src/galapagos/research/signal_selection/selection_rules.py",
    ]
    payload = {
        "version": display,
        **audit_signal_selection_leakage(
            rules=build_default_rules(),
            source_paths=[Path(path) for path in source_paths],
        ),
        "research_only": True,
        "codex_cli_called": False,
        "holdout_executed": False,
        "no_real_trading": True,
    }
    write_selection_report(
        stem="signal_selection_leakage_audit",
        version=version,
        payload=payload,
        title="Signal Selection Leakage Audit",
        lines=[
            f"Statut: {payload['status']}.",
            f"Colonnes futures interdites detectees: {payload['forbidden_future_columns']}.",
            f"Regles causales: {payload['causal_rules_count']}.",
            f"Regles diagnostic-only: {payload['diagnostic_rules_count']}.",
            "Les colonnes de resultat realise restent autorisees pour evaluation uniquement.",
            "Aucun Codex CLI, aucun holdout, aucun ordre reel.",
        ],
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
