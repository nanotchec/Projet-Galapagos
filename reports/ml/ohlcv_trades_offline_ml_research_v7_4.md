# Rapport qualite - V7.4 ML offline OHLCV + public trades

## Objectif

V7.4 entraine des baselines ML offline simples sur le dataset V7.3 valide avec OHLCV + public trades features.
Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.

## Fenetre

- Debut : `2023-03-25`.
- Fin : `2023-04-23`.
- Jours : `30`.

## Cible et modeles

- Cible : `up_down_flat_h1`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features ML : `71` colonnes causales OHLCV + aggTrades autorisees uniquement.
- `walk_forward_group` est conserve pour les metriques descriptives, jamais utilise comme feature.

## Outputs

- `1m` scores : `data/research/v7_4/ml/offline_research_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-04-23/ml-scores.parquet` (172560 lignes).
  - lignes ML utilisees : `43140`.
  - train/validation/test : `25860` / `8640` / `8640`.
  - groupes walk-forward : `5`.
- `5m` scores : `data/research/v7_4/ml/offline_research_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-04-23/ml-scores.parquet` (34320 lignes).
  - lignes ML utilisees : `8580`.
  - train/validation/test : `5124` / `1728` / `1728`.
  - groupes walk-forward : `5`.
- `15m` scores : `data/research/v7_4/ml/offline_research_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-04-23/ml-scores.parquet` (11280 lignes).
  - lignes ML utilisees : `2820`.
  - train/validation/test : `1668` / `576` / `576`.
  - groupes walk-forward : `5`.
- `1h` scores : `data/research/v7_4/ml/offline_research_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-04-23/ml-scores.parquet` (2640 lignes).
  - lignes ML utilisees : `660`.
  - train/validation/test : `372` / `144` / `144`.
  - groupes walk-forward : `5`.

## Sanity checks

- La cible unique est `up_down_flat_h1`.
- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.
- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `walk_forward_group`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.
- Les sorties sont nommees `research_*` et ne sont pas des signaux.
- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.
- Les metriques walk-forward sont descriptives et ne sont pas un backtest.
- Les comparaisons a V6.2/V5.4 sont descriptives, non actionnables et non directement comparables si les fenetres different.

## Limitations

- V7.4 entraine uniquement des baselines ML offline simples sur le dataset OHLCV + aggTrades V7.3.
- V7.4 utilise une fenetre bornee de 30 jours et ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Non-usage warnings

- V7.4 ne valide aucune strategie.
- V7.4 ne produit aucun backtest.
- V7.4 ne produit aucun signal de trading.
- V7.4 ne produit aucun ordre.
- V7.4 n'autorise aucun paper live.
- V7.4 n'autorise aucun trading reel.
- Les metriques sont descriptives et non actionnables.
- Les metriques walk-forward ne sont pas un backtest.
- La fenetre de 30 jours est trop courte pour une conclusion robuste.
- Les comparaisons V7.4 vs V6.2/V5.4 sont descriptives, non actionnables.
