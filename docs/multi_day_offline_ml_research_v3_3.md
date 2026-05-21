# Rapport qualite - V3.3 ML offline multi-day

## Objectif

V3.3 entraine des baselines ML offline simples sur le dataset multi-day V3.2 valide.
Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.

## Cible et modeles

- Cible : `up_down_flat_h1`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features : colonnes causales V3.0 autorisees uniquement.

## Outputs

- `1m` scores : `data/research/v3_3/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-15_2024-01-21/ml-scores.parquet` (40196 lignes).
  - lignes ML utilisees : `10049`.
  - train/validation/test : `6018` / `2016` / `2015`.
- `5m` scores : `data/research/v3_3/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-15_2024-01-21/ml-scores.parquet` (7940 lignes).
  - lignes ML utilisees : `1985`.
  - train/validation/test : `1179` / `403` / `403`.
- `15m` scores : `data/research/v3_3/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-15_2024-01-21/ml-scores.parquet` (2564 lignes).
  - lignes ML utilisees : `641`.
  - train/validation/test : `373` / `134` / `134`.
- `1h` scores : `data/research/v3_3/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-15_2024-01-21/ml-scores.parquet` (548 lignes).
  - lignes ML utilisees : `137`.
  - train/validation/test : `70` / `33` / `34`.

## Sanity checks

- La cible unique est `up_down_flat_h1`.
- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.
- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.
- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.

## Limitations

- V3.3 entraine uniquement des baselines ML offline simples sur le dataset multi-day V3.2 valide.
- V3.3 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Non-usage warnings

- V3.3 ne valide aucune strategie.
- V3.3 ne produit aucun backtest.
- V3.3 ne produit aucun signal de trading.
- V3.3 ne produit aucun ordre.
- V3.3 n'autorise aucun paper live.
- V3.3 n'autorise aucun trading reel.
- Les metriques sont descriptives et non actionnables.
