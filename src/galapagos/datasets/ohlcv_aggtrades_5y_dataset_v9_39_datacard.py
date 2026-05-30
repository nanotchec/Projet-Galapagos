from __future__ import annotations

from typing import Any


def build_dataset_datacard_v9_39(report: dict[str, Any]) -> str:
    return (
        "# Datacard V9.39 - OHLCV + AggTrades 5Y Dataset\n\n"
        "## Statut\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Dataset cree : `{report['dataset_created']}`.\n"
        f"- Target utilise : `{report['target_name']}`.\n"
        f"- Qualite : `{report['quality_status']}`.\n"
        f"- Couverture : `{report['coverage_status']}`.\n\n"
        "## Label readiness\n\n"
        "Aucun label strictement compatible avec la fenetre 5Y `2021-05-05 -> 2026-05-05` n'a ete trouve.\n"
        "V9.39 ne cree donc pas de faux dataset supervise et ne reutilise pas aveuglement les labels historiques.\n\n"
        "## Limites\n\n"
        "- Les labels V9.6/V9.12/V9.13 restent des candidats diagnostiques historiques sur une fenetre plus courte.\n"
        "- V9.39 ne valide aucune strategie, aucun signal, aucun backtest et aucun modele.\n"
        "- La suite recommandee est une label factory 5Y explicite avant tout dataset complet.\n"
    )
