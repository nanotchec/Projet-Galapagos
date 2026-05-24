from __future__ import annotations

from typing import Any

from galapagos.datasets.schemas import DATASET_COLUMNS_V6_1, TIMEFRAMES_V6_1


def build_quality_markdown_v6_1(manifest: dict[str, Any]) -> str:
    inputs = "\n".join(
        "\n".join(
            [
                f"- `{timeframe}` advanced features V6.0 : `{manifest['input_features'][timeframe]['path']}` ({manifest['input_features'][timeframe]['rows']} lignes)",
                f"- `{timeframe}` labels V5.2 : `{manifest['input_labels'][timeframe]['path']}` ({manifest['input_labels'][timeframe]['rows']} lignes)",
            ]
        )
        for timeframe in TIMEFRAMES_V6_1
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
        for timeframe in TIMEFRAMES_V6_1
    )
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Rapport qualite - V6.1 Dataset supervise offline advanced OHLCV

## Objectif

V6.1 assemble uniquement un dataset supervise offline en joignant les advanced OHLCV features V6.0 et les labels forward V5.2 deja valides sur la fenetre historique continue V5.0.
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
- Nombre de colonnes dataset : `{len(DATASET_COLUMNS_V6_1)}`
- Nombre de colonnes advanced features : `{manifest['advanced_feature_columns_count']}`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.
- `macd_like_signal` est une feature technique MACD-like, pas un signal de trading.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v6_1_preview`.
- Groupes walk-forward : `calendar_quarter`.

## Anti-leakage

- Les advanced features V6.0 et labels V5.2 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V6.1, jamais comme decision en ligne.

## Limitations

{limitations}

{_non_usage_markdown('V6.1')}
"""


def build_datacard_markdown_v6_1(manifest: dict[str, Any]) -> str:
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Data Card - Galapagos V6.1 Dataset supervise offline advanced OHLCV

- Dataset name : `advanced_ohlcv_offline_supervised_dataset_v6_1`
- Version : `{manifest['version']}`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : `{manifest['input_features_manifest']['window_start']}` a `{manifest['input_features_manifest']['window_end']}`.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Advanced OHLCV features V6.0, causales, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.
La colonne `macd_like_signal` est une feature technique MACD-like, pas un signal de trading.

## Labels inclus

Labels forward V5.2 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v6_1_preview`.
- Groupes walk-forward descriptifs : trimestre calendaire.

## Known Limitations

{limitations}

{_non_usage_markdown('V6.1')}
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
