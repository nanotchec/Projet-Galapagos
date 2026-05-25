# Rapport qualite - V8.0 ML offline OHLCV + public trades

## Objectif

V8.0 entraine des baselines ML offline simples sur le dataset V7.9 valide avec OHLCV + public trades features.
Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.

## Fenetre

- Debut : `2023-03-25`.
- Fin : `2023-06-22`.
- Jours : `90`.

## Cible et modeles

- Cible : `up_down_flat_h1`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features ML : `71` colonnes causales OHLCV + aggTrades autorisees uniquement.
- `walk_forward_group` est conserve pour les metriques descriptives, jamais utilise comme feature.

## Outputs

- `1m` scores : `data/research/v8_0/ml/offline_research_ohlcv_trades_90d/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2023-06-22/ml-scores.parquet` (518160 lignes).
  - lignes ML utilisees : `129540`.
  - train/validation/test : `77700` / `25920` / `25920`.
  - groupes walk-forward : `4`.
- `5m` scores : `data/research/v8_0/ml/offline_research_ohlcv_trades_90d/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2023-06-22/ml-scores.parquet` (103440 lignes).
  - lignes ML utilisees : `25860`.
  - train/validation/test : `15492` / `5184` / `5184`.
  - groupes walk-forward : `4`.
- `15m` scores : `data/research/v8_0/ml/offline_research_ohlcv_trades_90d/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2023-06-22/ml-scores.parquet` (34320 lignes).
  - lignes ML utilisees : `8580`.
  - train/validation/test : `5124` / `1728` / `1728`.
  - groupes walk-forward : `4`.
- `1h` scores : `data/research/v8_0/ml/offline_research_ohlcv_trades_90d/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2023-06-22/ml-scores.parquet` (8400 lignes).
  - lignes ML utilisees : `2100`.
  - train/validation/test : `1236` / `432` / `432`.
  - groupes walk-forward : `4`.

## Sanity checks

- La cible unique est `up_down_flat_h1`.
- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.
- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `walk_forward_group`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.
- Les sorties sont nommees `research_*` et ne sont pas des signaux.
- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.
- Les metriques walk-forward sont descriptives et ne sont pas un backtest.
- Les comparaisons a V7.4/V6.2/V5.4 sont descriptives, non actionnables et non directement comparables si les fenetres different.

## Limitations

- V8.0 entraine uniquement des baselines ML offline simples sur le dataset OHLCV + aggTrades 90 jours V7.9.
- V8.0 produit une robustesse descriptive et une falsification offline, sans backtest, sans strategie, sans signal de trading et sans ordre.
- La fenetre de 90 jours reste insuffisante pour conclure a une robustesse statistique forte.

## Non-usage warnings

- V8.0 ne valide aucune strategie.
- V8.0 ne produit aucun backtest.
- V8.0 ne produit aucun signal de trading.
- V8.0 ne produit aucun ordre.
- V8.0 n'autorise aucun paper live.
- V8.0 n'autorise aucun trading reel.
- Les metriques sont descriptives et non actionnables.
- Les metriques walk-forward ne sont pas un backtest.
- La fenetre de 90 jours est trop courte pour une conclusion robuste.
- Les comparaisons V8.0 vs V7.4/V6.2/V5.4 sont descriptives, non actionnables.
