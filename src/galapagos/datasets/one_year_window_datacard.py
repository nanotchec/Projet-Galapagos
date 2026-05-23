from __future__ import annotations

from typing import Any

from galapagos.datasets.schemas import DATASET_COLUMNS_V4_5, TIMEFRAMES_V4_5


def build_quality_markdown_v4_5(manifest: dict[str, Any]) -> str:
    inputs = "\n".join(
        "\n".join(
            [
                f"- `{timeframe}` features V4.3 : `{manifest['input_features'][timeframe]['path']}` ({manifest['input_features'][timeframe]['rows']} lignes)",
                f"- `{timeframe}` labels V4.4 : `{manifest['input_labels'][timeframe]['path']}` ({manifest['input_labels'][timeframe]['rows']} lignes)",
            ]
        )
        for timeframe in TIMEFRAMES_V4_5
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
        for timeframe in TIMEFRAMES_V4_5
    )
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Rapport qualite - V4.5 Dataset supervise offline 1 an

## Objectif

V4.5 assemble un dataset supervise offline 1 an en joignant les features causales V4.3 et les labels forward V4.4 deja valides.
Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.

## Inputs

{inputs}

## Outputs

{outputs}

## Schema

- Version schema : `{manifest['dataset_schema_version']}`
- Nombre de colonnes : `{len(DATASET_COLUMNS_V4_5)}`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v4_5_preview`.

## Anti-leakage

- Les features V4.3 et labels V4.4 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V4.5, jamais comme decision en ligne.

## Limitations

{limitations}

{_non_usage_markdown('V4.5')}
"""


def build_datacard_markdown_v4_5(manifest: dict[str, Any]) -> str:
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Data Card - Galapagos V4.5 Dataset supervise offline 1 an

- Dataset name : `one_year_offline_supervised_dataset_v4_5`
- Version : `{manifest['version']}`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : 2024-01-01 a 2024-12-31.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features causales V4.3 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.

## Labels inclus

Labels forward V4.4 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v4_5_preview`.

## Known Limitations

{limitations}

{_non_usage_markdown('V4.5')}
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
