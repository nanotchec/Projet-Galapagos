from __future__ import annotations

from typing import Any


def build_quality_markdown_v9_1(manifest: dict[str, Any]) -> str:
    lines = [
        "# Rapport qualite V9.1 - Dataset supervise raffine OHLCV + trades",
        "",
        "V9.1 assemble uniquement un dataset supervise offline a partir des features raffinees V9.0 et des labels V5.2 filtres sur la meme fenetre.",
        "V9.1 ne valide aucune strategie, ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.",
        "",
        "## Fenetre",
        "",
        f"- Debut : `{manifest['input_features_manifest']['window_start']}`.",
        f"- Fin : `{manifest['input_features_manifest']['window_end']}`.",
        f"- Total jours : `{manifest['input_features_manifest']['total_days']}`.",
        "",
        "## Sorties",
        "",
    ]
    for timeframe, output in manifest["outputs"].items():
        quality = manifest["quality"][timeframe]
        lines.extend(
            [
                f"### {timeframe}",
                "",
                f"- Dataset : `{output['path']}`.",
                f"- Rows : `{output['rows']}`.",
                f"- Split counts : `{quality['split_counts']}`.",
                f"- Warmup rows : `{quality['feature_warmup_rows']}`.",
                f"- Tail rows : `{quality['tail_rows']}`.",
                f"- Errors : `{quality['errors']}`.",
                f"- Warnings : `{quality['warnings']}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Interdits maintenus",
            "",
            "- Aucun backtest.",
            "- Aucune strategie.",
            "- Aucun signal de trading.",
            "- Aucun ordre.",
            "- Aucun paper live.",
            "- Aucun trading reel.",
            "",
            "V9.1 reste une etape de dataset offline non validee avant audit externe.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_datacard_markdown_v9_1(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Data Card V9.1 - Dataset supervise raffine OHLCV + trades",
            "",
            "## Usage",
            "",
            "Ce dataset est reserve a la recherche offline. Il contient des labels forward uniquement parce qu'il s'agit d'un assemblage supervise hors ligne.",
            "",
            "## Sources",
            "",
            f"- Features raffinees : `{manifest['input_features_manifest']['path']}`.",
            f"- Labels : `{manifest['input_labels_manifest']['path']}`.",
            "",
            "## Contraintes",
            "",
            "- Aucun usage trading n'est autorise par V9.1.",
            "- Les splits sont temporels et sans shuffle.",
            "- Les features sources ne sont pas modifiees.",
            "- Les labels sources ne sont pas modifies.",
            "",
            "## Limites",
            "",
            "\n".join(f"- {limitation}" for limitation in manifest["limitations"]),
            "",
        ]
    )
