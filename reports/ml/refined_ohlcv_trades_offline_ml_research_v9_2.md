# Rapport qualite - V9.2 ML offline raffine OHLCV + trades

V9.2 entraine des baselines ML offline simples sur le dataset raffine V9.1.
Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.

## Fenetre

- Debut : `2023-03-25`.
- Fin : `2024-03-24`.
- Jours : `366`.

## Cible et modeles

- Cible : `up_down_flat_h1`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features ML : `18` features raffinees selectionnees.
- `walk_forward_group` est conserve pour les metriques descriptives, jamais utilise comme feature.

## Outputs

- `1m` scores : `data/research/v9_2/ml/refined_offline_research_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2024-03-24/ml-scores.parquet` (2107920 lignes).
  - lignes ML utilisees : `526980`.
  - train/validation/test : `316164` / `105408` / `105408`.
  - groupes walk-forward : `13`.
- `5m` scores : `data/research/v9_2/ml/refined_offline_research_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2024-03-24/ml-scores.parquet` (421392 lignes).
  - lignes ML utilisees : `105348`.
  - train/validation/test : `63184` / `21082` / `21082`.
  - groupes walk-forward : `13`.
- `15m` scores : `data/research/v9_2/ml/refined_offline_research_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2024-03-24/ml-scores.parquet` (140304 lignes).
  - lignes ML utilisees : `35076`.
  - train/validation/test : `21021` / `7027` / `7028`.
  - groupes walk-forward : `13`.
- `1h` scores : `data/research/v9_2/ml/refined_offline_research_ohlcv_trades/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2024-03-24/ml-scores.parquet` (34896 lignes).
  - lignes ML utilisees : `8724`.
  - train/validation/test : `5210` / `1757` / `1757`.
  - groupes walk-forward : `13`.

## Interdits maintenus

- V9.2 ne valide aucune strategie.
- V9.2 ne produit aucun backtest.
- V9.2 ne produit aucun signal de trading.
- V9.2 ne produit aucun ordre.
- V9.2 ne persiste aucun modele.
- V9.2 n'autorise aucun paper live ni trading reel.

Les metriques sont descriptives et non actionnables.
