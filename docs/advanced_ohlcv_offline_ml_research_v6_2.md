# Rapport qualite - V6.2 ML offline historique max

## Objectif

V6.2 entraine des baselines ML offline simples sur le dataset V6.1 valide avec advanced OHLCV features.
Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.

## Fenetre

- Debut : `2023-03-25`.
- Fin : `2026-05-23`.
- Jours : `1156`.

## Cible et modeles

- Cible : `up_down_flat_h1`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features : `158` colonnes advanced OHLCV causales V6.0 autorisees uniquement.
- `macd_like_signal` est une feature technique MACD-like autorisee, pas un signal de trading.
- `walk_forward_group` est conserve pour les metriques descriptives, jamais utilise comme feature.

## Outputs

- `1m` scores : `data/research/v6_2/ml/offline_research_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/ml-scores.parquet` (6657492 lignes).
  - lignes ML utilisees : `1664373`.
  - train/validation/test : `998518` / `332928` / `332927`.
  - groupes walk-forward : `14`.
- `5m` scores : `data/research/v6_2/ml/offline_research_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/ml-scores.parquet` (1330752 lignes).
  - lignes ML utilisees : `332688`.
  - train/validation/test : `199517` / `66585` / `66586`.
  - groupes walk-forward : `14`.
- `15m` scores : `data/research/v6_2/ml/offline_research_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/ml-scores.parquet` (442944 lignes).
  - lignes ML utilisees : `110736`.
  - train/validation/test : `66346` / `22195` / `22195`.
  - groupes walk-forward : `14`.
- `1h` scores : `data/research/v6_2/ml/offline_research_advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/ml-scores.parquet` (110016 lignes).
  - lignes ML utilisees : `27504`.
  - train/validation/test : `16407` / `5548` / `5549`.
  - groupes walk-forward : `13`.

## Sanity checks

- La cible unique est `up_down_flat_h1`.
- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.
- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `walk_forward_group`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.
- Les sorties sont nommees `research_*` et ne sont pas des signaux.
- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.
- Les metriques walk-forward sont descriptives et ne sont pas un backtest.
- La comparaison V6.2 vs V5.4 est descriptive, non actionnable et sans conclusion de trading.

## Limitations

- V6.2 entraine uniquement des baselines ML offline simples sur le dataset V6.1 avec advanced OHLCV features.
- V6.2 compare descriptivement les resultats aux baselines V5.4 simple OHLCV si disponibles, sans produire de backtest, de strategie, de signal de trading ni d'ordre.

## Non-usage warnings

- V6.2 ne valide aucune strategie.
- V6.2 ne produit aucun backtest.
- V6.2 ne produit aucun signal de trading.
- V6.2 ne produit aucun ordre.
- V6.2 n'autorise aucun paper live.
- V6.2 n'autorise aucun trading reel.
- Les metriques sont descriptives et non actionnables.
- Les metriques walk-forward ne sont pas un backtest.
- La comparaison V6.2 vs V5.4 est descriptive, non actionnable.
