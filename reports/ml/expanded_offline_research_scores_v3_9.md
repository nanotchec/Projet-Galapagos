# Rapport qualite - V3.9 ML offline 90 jours

## Objectif

V3.9 entraine des baselines ML offline simples sur le dataset 90 jours V3.8 valide.
Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.

## Cible et modeles

- Cible : `up_down_flat_h1`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features : colonnes causales V3.6 autorisees uniquement.

## Outputs

- `1m` scores : `data/research/v3_9/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-03-30/ml-scores.parquet` (518276 lignes).
  - lignes ML utilisees : `129569`.
  - train/validation/test : `77730` / `25920` / `25919`.
- `5m` scores : `data/research/v3_9/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-03-30/ml-scores.parquet` (103556 lignes).
  - lignes ML utilisees : `25889`.
  - train/validation/test : `15522` / `5184` / `5183`.
- `15m` scores : `data/research/v3_9/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-03-30/ml-scores.parquet` (34436 lignes).
  - lignes ML utilisees : `8609`.
  - train/validation/test : `5154` / `1728` / `1727`.
- `1h` scores : `data/research/v3_9/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-03-30/ml-scores.parquet` (8516 lignes).
  - lignes ML utilisees : `2129`.
  - train/validation/test : `1266` / `432` / `431`.

## Sanity checks

- La cible unique est `up_down_flat_h1`.
- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.
- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.
- Les sorties sont nommees `research_*` et ne sont pas des signaux.
- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.

## Limitations

- V3.9 entraine uniquement des baselines ML offline simples sur le dataset 90 jours V3.8 valide.
- V3.9 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Non-usage warnings

- V3.9 ne valide aucune strategie.
- V3.9 ne produit aucun backtest.
- V3.9 ne produit aucun signal de trading.
- V3.9 ne produit aucun ordre.
- V3.9 n'autorise aucun paper live.
- V3.9 n'autorise aucun trading reel.
- Les metriques sont descriptives et non actionnables.
