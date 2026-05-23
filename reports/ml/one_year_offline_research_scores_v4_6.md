# Rapport qualite - V4.6 ML offline 1 an

## Objectif

V4.6 entraine des baselines ML offline simples sur le dataset 1 an V4.5 valide.
Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.

## Cible et modeles

- Cible : `up_down_flat_h1`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features : colonnes causales V4.3 autorisees uniquement.

## Outputs

- `1m` scores : `data/research/v4_6/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-12-31/ml-scores.parquet` (2108036 lignes).
  - lignes ML utilisees : `527009`.
  - train/validation/test : `316194` / `105408` / `105407`.
- `5m` scores : `data/research/v4_6/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-12-31/ml-scores.parquet` (421508 lignes).
  - lignes ML utilisees : `105377`.
  - train/validation/test : `63214` / `21082` / `21081`.
- `15m` scores : `data/research/v4_6/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-12-31/ml-scores.parquet` (140420 lignes).
  - lignes ML utilisees : `35105`.
  - train/validation/test : `21051` / `7027` / `7027`.
- `1h` scores : `data/research/v4_6/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-12-31/ml-scores.parquet` (35012 lignes).
  - lignes ML utilisees : `8753`.
  - train/validation/test : `5240` / `1757` / `1756`.

## Sanity checks

- La cible unique est `up_down_flat_h1`.
- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.
- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.
- Les sorties sont nommees `research_*` et ne sont pas des signaux.
- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.

## Limitations

- V4.6 entraine uniquement des baselines ML offline simples sur le dataset 1 an V4.5 valide.
- V4.6 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Non-usage warnings

- V4.6 ne valide aucune strategie.
- V4.6 ne produit aucun backtest.
- V4.6 ne produit aucun signal de trading.
- V4.6 ne produit aucun ordre.
- V4.6 n'autorise aucun paper live.
- V4.6 n'autorise aucun trading reel.
- Les metriques sont descriptives et non actionnables.
