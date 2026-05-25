from __future__ import annotations

from typing import Any

from galapagos.datasets.schemas import DATASET_COLUMNS_V8_4, TIMEFRAMES_V8_4


def build_quality_markdown_v8_4(manifest: dict[str, Any]) -> str:
    inputs = "\n".join(
        "\n".join(
            [
                f"- `{timeframe}` features OHLCV+trades V8.3 : `{manifest['input_features'][timeframe]['path']}` ({manifest['input_features'][timeframe]['rows']} lignes)",
                f"- `{timeframe}` labels V5.2 filtres : `{manifest['input_labels_filtered'][timeframe]['rows']}` lignes",
            ]
        )
        for timeframe in TIMEFRAMES_V8_4
    )
    outputs = "\n".join(
        "\n".join(
            [
                f"- `{timeframe}` dataset : `{manifest['outputs'][timeframe]['path']}` ({manifest['outputs'][timeframe]['rows']} lignes)",
                f"- `{timeframe}` splits : `{manifest['splits'][timeframe]['path']}` ({manifest['splits'][timeframe]['rows']} lignes)",
                f"  - splits : `{manifest['quality'][timeframe]['split_counts']}`",
                f"  - groupes walk-forward : `{manifest['quality'][timeframe]['walk_forward_group_counts']}`",
                f"  - warmup rows : `{manifest['quality'][timeframe]['feature_warmup_rows']}`",
                f"  - tail rows : `{manifest['quality'][timeframe]['tail_rows']}`",
            ]
        )
        for timeframe in TIMEFRAMES_V8_4
    )
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Rapport qualite - V8.4 Dataset supervise offline OHLCV + trades

## Objectif

V8.4 assemble uniquement un dataset supervise offline multi-source en joignant les features causales OHLCV + aggTrades V8.3 et les labels forward V5.2 filtres sur la meme fenetre d'environ 1 an.
Cette preview ne fait aucun entrainement ML et ne produit aucune sortie operationnelle.

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
- Nombre de colonnes dataset : `{len(DATASET_COLUMNS_V8_4)}`
- Nombre de colonnes features OHLCV+trades : `{manifest['feature_columns_count']}`
- Le schema est strictement ordonne et refuse toute colonne supplementaire.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Shuffle : false.
- Purge/embargo : `none_v8_4_preview`.
- Groupes walk-forward : groupes calendaires mensuels descriptifs.

## Anti-leakage

- Les features V8.3 et labels V5.2 restent des fichiers sources separes.
- Les hashes `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est controle.
- `label_available_ts > decision_ts` est controle pour les labels valides.
- Les labels sont inclus uniquement dans un dataset offline V8.4, jamais comme decision en ligne.

## Limitations

{limitations}

{_non_usage_markdown('V8.4')}
"""


def build_datacard_markdown_v8_4(manifest: dict[str, Any]) -> str:
    limitations = "\n".join(f"- {item}" for item in manifest["limitations"])
    return f"""# Data Card - Galapagos V8.4 Dataset supervise offline OHLCV + trades

- Dataset name : `ohlcv_trades_1y_offline_supervised_dataset_v8_4`
- Version : `{manifest['version']}`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : `{manifest['input_features_manifest']['window_start']}` a `{manifest['input_features_manifest']['window_end']}`.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features OHLCV + aggTrades V8.3, causales, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.
Les features trades sont des variables de recherche, pas des signaux de trading.

## Labels inclus

Labels forward V5.2 filtres sur la fenetre V8.3, horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v8_4_preview`.
- Groupes walk-forward descriptifs : groupes calendaires mensuels de `wf_2023_03_partial` a `wf_2024_03_partial`.

## Known Limitations

{limitations}

- La fenetre d'environ 1 an permet une analyse plus serieuse que 90 jours, mais ne constitue pas a elle seule une preuve de performance trading.

{_non_usage_markdown('V8.4')}
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
