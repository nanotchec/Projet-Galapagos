# Rapport qualite - V8.5 ML offline OHLCV + public trades

## Objectif

V8.5 entraine des baselines ML offline simples sur le dataset V8.4 valide avec OHLCV + public trades features.
Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.

## Fenetre

- Debut : `2023-03-25`.
- Fin : `2024-03-24`.
- Jours : `366`.

## Cible et modeles

- Cible : `up_down_flat_h1`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features ML : `71` colonnes causales OHLCV + aggTrades autorisees uniquement.
- `walk_forward_group` est conserve pour les metriques descriptives, jamais utilise comme feature.

## Outputs

- `1m` scores : `data/research/v8_5/ml/offline_research_ohlcv_trades_1y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/ml-scores.parquet` (2107920 lignes).
  - lignes ML utilisees : `526980`.
  - train/validation/test : `316164` / `105408` / `105408`.
  - groupes walk-forward : `13`.
- `5m` scores : `data/research/v8_5/ml/offline_research_ohlcv_trades_1y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/ml-scores.parquet` (421392 lignes).
  - lignes ML utilisees : `105348`.
  - train/validation/test : `63184` / `21082` / `21082`.
  - groupes walk-forward : `13`.
- `15m` scores : `data/research/v8_5/ml/offline_research_ohlcv_trades_1y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/ml-scores.parquet` (140304 lignes).
  - lignes ML utilisees : `35076`.
  - train/validation/test : `21021` / `7027` / `7028`.
  - groupes walk-forward : `13`.
- `1h` scores : `data/research/v8_5/ml/offline_research_ohlcv_trades_1y/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/ml-scores.parquet` (34896 lignes).
  - lignes ML utilisees : `8724`.
  - train/validation/test : `5210` / `1757` / `1757`.
  - groupes walk-forward : `13`.

## Sanity checks

- La cible unique est `up_down_flat_h1`.
- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.
- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `walk_forward_group`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.
- Les sorties sont nommees `research_*` et ne sont pas des signaux.
- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.
- Les metriques walk-forward sont descriptives et ne sont pas un backtest.
- Les comparaisons a V8.0/V7.4/V6.2/V5.4 sont descriptives, non actionnables et non directement comparables si les fenetres different.

## Limitations

- V8.5 entraine uniquement des baselines ML offline simples sur le dataset OHLCV + aggTrades 1 an V8.4.
- V8.5 produit des metriques descriptives et non actionnables, sans backtest, sans strategie, sans signal de trading et sans ordre.

## Non-usage warnings

- V8.5 ne valide aucune strategie.
- V8.5 ne produit aucun backtest.
- V8.5 ne produit aucun signal de trading.
- V8.5 ne produit aucun ordre.
- V8.5 n'autorise aucun paper live.
- V8.5 n'autorise aucun trading reel.
- Les metriques sont descriptives et non actionnables.
- Les metriques walk-forward ne sont pas un backtest.
- La fenetre de 1 an est trop courte pour une conclusion robuste.
- Les comparaisons V8.5 vs V8.0/V7.4/V6.2/V5.4 sont descriptives, non actionnables.
