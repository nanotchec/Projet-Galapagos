from __future__ import annotations

from typing import Any

from galapagos.datasets.schemas import DATASET_COLUMNS_V3_8, TIMEFRAMES_V3_8


def build_quality_markdown_v3_8(manifest: dict[str, Any]) -> str:
    inputs = "\n".join(
        "\n".join(
            [
                f"- `{timeframe}` features V3.6 : `{manifest['input_features'][timeframe]['path']}` ({manifest['input_features'][timeframe]['rows']} lignes)",
                f"- `{timeframe}` labels V3.7 : `{manifest['input_labels'][timeframe]['path']}` ({manifest['input_labels'][timeframe]['rows']} lignes)",
            ]
        )
        for timeframe in TIMEFRAMES_V3_8
    )
    outputs = "\n".join(
        "\n".join(
            [
                f"- `{timeframe}` dataset : `{manifest['outputs'][timeframe]['path']}` ({manifest['outputs'][timeframe]['rows']} lignes)",
                f"- `{timeframe}` splits : `{manifest['splits'][timeframe]['path']}` ({manifest['splits'][timeframe]['rows']} lignes)",
                f"  - splits : `{manifest['quality'][timeframe]['split_counts']}`",
                f"  - warmup rows : `{manifest['quality'][timeframe]['feature_warmup_rows']}`",
                f"  - tail rows : `{manifest['quality'][timeframe]['tail_rows']}`",
            ]
        )
        for timeframe in TIMEFRAMES_V3_8
    )
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Rapport qualite - V3.8 Dataset supervise offline 90 jours

## Objectif

V3.8 assemble un dataset supervise offline 90 jours en joignant les features causales V3.6 et les labels forward V3.7 deja valides.
Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.

## Inputs

{inputs}

## Outputs

{outputs}

## Schema

- Version schema : `{manifest['dataset_schema_version']}`
- Nombre de colonnes : `{len(DATASET_COLUMNS_V3_8)}`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v3_8_preview`.

## Anti-leakage

- Les features V3.6 et labels V3.7 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V3.8, jamais comme decision en ligne.

## Limitations

{limitations}

{_non_usage_markdown('V3.8')}
"""


def build_datacard_markdown_v3_8(manifest: dict[str, Any]) -> str:
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Data Card - Galapagos V3.8 Dataset supervise offline 90 jours

- Dataset name : `expanded_offline_supervised_dataset_v3_8`
- Version : `{manifest['version']}`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : 2024-01-01 a 2024-03-30.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features causales V3.6 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.

## Labels inclus

Labels forward V3.7 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v3_8_preview`.

## Known Limitations

{limitations}

{_non_usage_markdown('V3.8')}
"""


def _non_usage_markdown(version: str) -> str:
    return f"""## Non-usage Warnings

- {version} ne valide aucune strategie.
- {version} ne produit aucun modele ML.
- {version} ne produit aucun backtest.
- {version} ne produit aucun signal de trading.
- {version} ne produit aucun ordre.
- {version} n'autorise aucun paper live.
- {version} n'autorise aucun trading reel.
"""
