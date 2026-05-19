# V2.7 — Offline Supervised Dataset Assembly Preview

## Correction V2.7.1

V2.7.1 est une correction runtime-only. V2.7 a été refusée en strict uniquement parce que `tests/validation/test_offline_supervised_dataset_v2_7_validator.py` ne terminait pas assez vite en audit externe. V2.7.1 conserve les artefacts dataset V2.7, garde le validateur de production strict, et rend le fichier complet de tests du validateur fiable sans ajouter de ML, modèle, backtest, paper live, ordre ou trading réel.

## Objectif

V2.7 construit une preview de dataset supervise offline en joignant les features causales V2.5 et les labels forward V2.6 deja valides.

Cette version reste strictement data/research offline. Elle ne cree aucun modele ML, aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Entrees

- Features V2.5 : `data/gold/features/ohlcv/.../features-2024-01-15.parquet`
- Labels V2.6 : `data/gold/labels/forward_returns/.../labels-2024-01-15.parquet`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Periode : BTCUSDT spot, 2024-01-15 uniquement

Avant assemblage, V2.7 relance les validateurs V2.3, V2.4, V2.5 et V2.6.

## Regle de jointure

La jointure est strictement effectuee sur :

- `source`
- `venue`
- `market_type`
- `symbol`
- `timeframe`
- `event_ts`
- `close_ts`
- `available_ts`
- `decision_ts`

V2.7 ne joint pas sur `label_available_ts`, `future_close` ou une colonne non causale.

## Sorties

Les datasets sont ecrits sous :

`data/gold/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=<tf>/year=2024/month=01/dataset-2024-01-15.parquet`

Les splits sont ecrits sous le meme dossier avec :

`splits-2024-01-15.parquet`

## Splits temporels

- Train : premiers 60 % temporels
- Validation : 20 % suivants
- Test : derniers 20 %
- Aucun shuffle
- `purge_embargo_group = none_v2_7_preview`

Comme V2.7 couvre une seule journee, ces splits sont une preview technique, pas une preuve statistique.

## Anti-leakage

- Les fichiers features et labels restent separes.
- Le dataset contient les labels uniquement parce qu'il s'agit d'un dataset offline.
- `source_features_sha256` et `source_labels_sha256` sont recalcules physiquement.
- `feature_available_ts <= decision_ts` est obligatoire.
- `label_available_ts > decision_ts` est obligatoire pour les labels valides.
- Les colonnes `prediction`, `model_score`, `signal`, `strategy`, `order`, `pnl`, `backtest`, `execution` et assimilables sont interdites.

## Securite

- V2.7 ne valide aucune strategie.
- V2.7 ne produit aucun modele ML.
- V2.7 ne produit aucun backtest.
- V2.7 ne produit aucun signal de trading.
- V2.7 ne produit aucun ordre.
- V2.7 n'autorise aucun paper live.
- V2.7 n'autorise aucun trading reel.
- V2.7.1 reste candidate `pending_external_audit`.
