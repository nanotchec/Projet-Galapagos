from __future__ import annotations

from typing import Any

from galapagos.datasets.schemas import DATASET_COLUMNS_V3_2, TIMEFRAMES_V3_2


def build_quality_markdown_v3_2(manifest: dict[str, Any]) -> str:
    lines = [
        "# Rapport qualite - V3.2 Dataset supervise offline multi-day",
        "",
        "## Objectif",
        "",
        "V3.2 assemble un dataset supervise offline multi-day en joignant les features causales V3.0 et les labels forward V3.1 deja valides.",
        "Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.",
        "",
        "## Inputs",
        "",
    ]
    for timeframe in TIMEFRAMES_V3_2:
        feature = manifest["input_features"][timeframe]
        label = manifest["input_labels"][timeframe]
        lines.append(f"- `{timeframe}` features V3.0 : `{feature['path']}` ({feature['rows']} lignes)")
        lines.append(f"- `{timeframe}` labels V3.1 : `{label['path']}` ({label['rows']} lignes)")

    lines.extend(["", "## Outputs", ""])
    for timeframe in TIMEFRAMES_V3_2:
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
            f"- Nombre de colonnes : `{len(DATASET_COLUMNS_V3_2)}`",
            "- Le schema est strictement ordonne et refuse toute colonne supplementaire.",
            "",
            "## Split Policy",
            "",
            "- Train : premiers 60 % temporels.",
            "- Validation : 20 % suivants.",
            "- Test : derniers 20 %.",
            "- Shuffle : false.",
            "- Purge/embargo : `none_v3_2_preview`.",
            "",
            "## Anti-leakage",
            "",
            "- Les features V3.0 et labels V3.1 restent des fichiers sources separes.",
            "- Les hashes source_features_sha256 et source_labels_sha256 sont recalcules physiquement.",
            "- `feature_available_ts <= decision_ts` est controle.",
            "- `label_available_ts > decision_ts` est controle pour les labels valides.",
            "- Les labels sont inclus uniquement dans un dataset offline V3.2, jamais comme decision en ligne.",
            "",
            "## Limitations",
            "",
        ]
    )
    for limitation in manifest["limitations"]:
        lines.append(f"- {limitation}")

    lines.extend(_non_usage_lines("V3.2"))
    return "\n".join(lines) + "\n"


def build_datacard_markdown_v3_2(manifest: dict[str, Any]) -> str:
    lines = [
        "# Data Card - Galapagos V3.2 Dataset supervise offline multi-day",
        "",
        "- Dataset name : `multi_day_offline_supervised_dataset_v3_2`",
        f"- Version : `{manifest['version']}`",
        "- Statut : `pending_external_audit`.",
        "- Source : Binance public archive read-only, BTCUSDT spot.",
        "- Periode : 2024-01-15 a 2024-01-21.",
        "- Timeframes : 1m, 5m, 15m, 1h.",
        "",
        "## Features incluses",
        "",
        "Features causales V3.0 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.",
        "",
        "## Labels inclus",
        "",
        "Labels forward V3.1 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.",
        "",
        "## Split Policy",
        "",
        "- Train : premiers 60 % temporels.",
        "- Validation : 20 % suivants.",
        "- Test : derniers 20 %.",
        "- Aucun shuffle.",
        "- Purge/embargo : `none_v3_2_preview`.",
        "",
        "## Known Limitations",
        "",
    ]
    for limitation in manifest["limitations"]:
        lines.append(f"- {limitation}")
    lines.extend(_non_usage_lines("V3.2"))
    return "\n".join(lines) + "\n"


def _non_usage_lines(version: str) -> list[str]:
    return [
        "",
        "## Non-usage Warnings",
        "",
        f"- {version} ne valide aucune strategie.",
        f"- {version} ne produit aucun modele ML.",
        f"- {version} ne produit aucun backtest.",
        f"- {version} ne produit aucun signal de trading.",
        f"- {version} ne produit aucun ordre.",
        f"- {version} n'autorise aucun paper live.",
        f"- {version} n'autorise aucun trading reel.",
    ]
