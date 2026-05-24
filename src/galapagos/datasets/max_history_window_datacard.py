from __future__ import annotations

from typing import Any

from galapagos.datasets.schemas import DATASET_COLUMNS_V5_3, TIMEFRAMES_V5_3


def build_quality_markdown_v5_3(manifest: dict[str, Any]) -> str:
    inputs = "\n".join(
        "\n".join(
            [
                f"- `{timeframe}` features V5.1 : `{manifest['input_features'][timeframe]['path']}` ({manifest['input_features'][timeframe]['rows']} lignes)",
                f"- `{timeframe}` labels V5.2 : `{manifest['input_labels'][timeframe]['path']}` ({manifest['input_labels'][timeframe]['rows']} lignes)",
            ]
        )
        for timeframe in TIMEFRAMES_V5_3
    )
    outputs = "\n".join(
        "\n".join(
            [
                f"- `{timeframe}` dataset : `{manifest['outputs'][timeframe]['path']}` ({manifest['outputs'][timeframe]['rows']} lignes)",
                f"- `{timeframe}` splits : `{manifest['splits'][timeframe]['path']}` ({manifest['splits'][timeframe]['rows']} lignes)",
                f"  - splits : `{manifest['quality'][timeframe]['split_counts']}`",
                f"  - groupes walk-forward : `{len(manifest['quality'][timeframe]['walk_forward_group_counts'])}`",
                f"  - warmup rows : `{manifest['quality'][timeframe]['feature_warmup_rows']}`",
                f"  - tail rows : `{manifest['quality'][timeframe]['tail_rows']}`",
            ]
        )
        for timeframe in TIMEFRAMES_V5_3
    )
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Rapport qualite - V5.3 Dataset supervise offline historique max

## Objectif

V5.3 assemble uniquement un dataset supervise offline en joignant les features causales V5.1 et les labels forward V5.2 deja valides sur la fenetre historique continue V5.0.
Cette preview ne fait aucun entrainement ML et ne produit aucun signal operationnel.

## Fenetre

- Debut : `{manifest['input_features_manifest']['window_start']}`
- Fin : `{manifest['input_features_manifest']['window_end']}`
- Nombre de jours : `{manifest['input_features_manifest']['total_days']}`

## Inputs

{inputs}

## Outputs

{outputs}

## Schema

- Version schema : `{manifest['dataset_schema_version']}`
- Nombre de colonnes dataset : `{len(DATASET_COLUMNS_V5_3)}`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v5_3_preview`.
- Groupes walk-forward : `calendar_quarter`.

## Anti-leakage

- Les features V5.1 et labels V5.2 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V5.3, jamais comme decision en ligne.

## Limitations

{limitations}

{_non_usage_markdown('V5.3')}
"""


def build_datacard_markdown_v5_3(manifest: dict[str, Any]) -> str:
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Data Card - Galapagos V5.3 Dataset supervise offline historique max

- Dataset name : `max_history_offline_supervised_dataset_v5_3`
- Version : `{manifest['version']}`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : `{manifest['input_features_manifest']['window_start']}` a `{manifest['input_features_manifest']['window_end']}`.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features causales V5.1 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.

## Labels inclus

Labels forward V5.2 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v5_3_preview`.
- Groupes walk-forward descriptifs : trimestre calendaire.

## Known Limitations

{limitations}

{_non_usage_markdown('V5.3')}
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
