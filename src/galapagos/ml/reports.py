from __future__ import annotations

from typing import Any


def build_ml_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Rapport ML offline V2.8",
        "",
        "## Objectif",
        "",
        "V2.8 entraine uniquement des baselines ML offline simples sur le dataset supervise V2.7 valide.",
        "Ces sorties sont des artefacts de recherche descriptifs, non actionnables.",
        "",
        "## Target",
        "",
        f"- Target : `{manifest['target_name']}`",
        "- Lignes utilisees : `label_valid_h1 = true` et `warmup_row = false`.",
        "",
        "## Features",
        "",
    ]
    for feature in manifest["feature_columns"]:
        lines.append(f"- `{feature}`")
    lines.extend(["", "## Modeles", ""])
    for model in manifest["models"]:
        lines.append(f"- `{model}`")
    lines.extend(["", "## Qualite", ""])
    for timeframe, quality in manifest["quality"].items():
        lines.append(
            f"- `{timeframe}` : {quality['rows_used_for_ml']} lignes ML, "
            f"train={quality['train_rows']}, validation={quality['validation_rows']}, test={quality['test_rows']}"
        )
    lines.extend(["", "## Limitations", ""])
    for limitation in manifest["limitations"]:
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "",
            "## Securite",
            "",
            "- V2.8 ne valide aucune strategie.",
            "- V2.8 ne produit aucun backtest.",
            "- V2.8 ne produit aucun signal de trading.",
            "- V2.8 ne produit aucun ordre.",
            "- V2.8 n'autorise aucun paper live.",
            "- V2.8 n'autorise aucun trading reel.",
            "- Les metriques sont descriptives et non actionnables.",
        ]
    )
    return "\n".join(lines) + "\n"

