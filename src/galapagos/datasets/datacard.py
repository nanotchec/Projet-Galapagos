from __future__ import annotations

from typing import Any

from galapagos.datasets.schemas import DATASET_COLUMNS_V2_7, TARGET_TIMEFRAMES


def build_quality_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Rapport qualite - V2.7 Offline Supervised Dataset",
        "",
        "## Correction V2.7.1",
        "",
        "V2.7.1 conserve les artefacts physiques V2.7. La correction porte sur le runtime du fichier complet de tests du validateur V2.7, sans relacher le validateur de production.",
        "",
        "## Objectif",
        "",
        "V2.7 assemble un dataset supervise offline en joignant les features causales V2.5 et les labels forward V2.6 deja valides.",
        "Cette version ne fait aucune estimation de modele et ne produit aucun signal operationnel.",
        "",
        "## Inputs",
        "",
    ]
    for timeframe in TARGET_TIMEFRAMES:
        feature = manifest["input_features"][timeframe]
        label = manifest["input_labels"][timeframe]
        lines.append(f"- `{timeframe}` features : `{feature['path']}` ({feature['rows']} lignes)")
        lines.append(f"- `{timeframe}` labels : `{label['path']}` ({label['rows']} lignes)")

    lines.extend(["", "## Outputs", ""])
    for timeframe in TARGET_TIMEFRAMES:
        output = manifest["outputs"][timeframe]
        split = manifest["splits"][timeframe]
        quality = manifest["quality"][timeframe]
        lines.append(f"- `{timeframe}` dataset : `{output['path']}` ({output['rows']} lignes)")
        lines.append(f"- `{timeframe}` splits : `{split['path']}` ({split['rows']} lignes)")
        lines.append(f"  - splits : `{quality['split_counts']}`")
        lines.append(f"  - tail rows : `{quality['tail_rows']}`")

    lines.extend(
        [
            "",
            "## Schema",
            "",
            f"- Version schema : `{manifest['dataset_schema_version']}`",
            f"- Nombre de colonnes : `{len(DATASET_COLUMNS_V2_7)}`",
            "- Le schema est strictement ordonne et refuse toute colonne supplementaire.",
            "",
            "## Split Policy",
            "",
            "- Train : 60 %",
            "- Validation : 20 %",
            "- Test : 20 %",
            "- Shuffle : false",
            "- Purge/embargo : `none_v2_7_preview`",
            "",
            "## Anti-leakage",
            "",
            "- Les features et labels restent des fichiers sources separes.",
            "- Les hashes source_features_sha256 et source_labels_sha256 sont recalcules physiquement.",
            "- `feature_available_ts <= decision_ts` est controle.",
            "- `label_available_ts > decision_ts` est controle pour les labels valides.",
            "",
            "## Limitations",
            "",
        ]
    )
    for limitation in manifest["limitations"]:
        lines.append(f"- {limitation}")

    lines.extend(
        [
            "",
            "## Securite",
            "",
            "- V2.7 ne valide aucune strategie.",
            "- V2.7 ne produit aucun modele ML.",
            "- V2.7 ne produit aucun backtest.",
            "- V2.7 ne produit aucun signal de trading.",
            "- V2.7 ne produit aucun ordre.",
            "- V2.7 n'autorise aucun paper live.",
            "- V2.7 n'autorise aucun trading reel.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_datacard_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Data Card - Galapagos V2.7 Offline Supervised Dataset",
        "",
        "- Dataset name : `offline_supervised_dataset_v2_7`",
        f"- Version : `{manifest['version']}`",
        "- Correction candidate : `V2.7.1` runtime validator tests, pending external audit.",
        "- Source : Binance public archive read-only, BTCUSDT spot.",
        "- Periode : 2024-01-15 uniquement.",
        "- Timeframes : 1m, 5m, 15m, 1h.",
        "",
        "## Features incluses",
        "",
        "Features causales V2.5 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.",
        "",
        "## Labels inclus",
        "",
        "Labels forward V2.6 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.",
        "",
        "## Split Policy",
        "",
        "- Train : premiers 60 % temporels.",
        "- Validation : 20 % suivants.",
        "- Test : derniers 20 %.",
        "- Aucun shuffle.",
        "",
        "## Known Limitations",
        "",
    ]
    for limitation in manifest["limitations"]:
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "",
            "## Non-usage Warnings",
            "",
            "- V2.7 ne valide aucune strategie.",
            "- V2.7 ne produit aucun modele ML.",
            "- V2.7 ne produit aucun backtest.",
            "- V2.7 ne produit aucun signal de trading.",
            "- V2.7 ne produit aucun ordre.",
            "- V2.7 n'autorise aucun paper live.",
            "- V2.7 n'autorise aucun trading reel.",
        ]
    )
    return "\n".join(lines) + "\n"
