from __future__ import annotations

import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.provider_decision_matrix import build_provider_decision_matrix
from galapagos.research.report_models import write_research_report


def main() -> None:
    payload = build_provider_decision_matrix()
    write_research_report(
        name="data_provider_matrix_v1_14",
        payload=payload,
        title="Data Provider Decision Matrix V1.14",
        lines=[
            f"Verdicts: {', '.join(payload['verdicts'])}.",
            "Aucun achat provider n'est justifie maintenant.",
            "Les prix precis restent a verifier manuellement.",
        ],
    )
    _write_doc(payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _write_doc(payload: dict) -> None:
    lines = [
        "# Data Provider Decision Matrix",
        "",
        "Cette matrice compare les sources de donnees derivees pour Galapagos.",
        (
            "Les couts exacts ne sont pas inventes: ils restent `requires manual check` "
            "quand ils ne sont pas verifies."
        ),
        "",
        "## Decision actuelle",
        "",
        (
            "Ne pas acheter de provider tant que les donnees publiques ne montrent pas "
            "un signal derive robuste."
        ),
        "",
        "## Providers",
        "",
    ]
    for provider in payload["providers"]:
        lines.extend(
            [
                f"### {provider['provider']}",
                "",
                f"- Cout mensuel: {provider['monthly_cost']}",
                f"- Funding: {provider['funding_history']}",
                f"- Open interest: {provider['open_interest_history']}",
                f"- Liquidations: {provider['liquidations_history']}",
                f"- Agregat multi-exchange: {provider['multi_exchange_aggregate']}",
                f"- Score priorite: {provider['priority_score']}",
                f"- Note: {provider['notes']}",
                "",
            ]
        )
    from pathlib import Path

    Path("docs/data_provider_decision_matrix.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
