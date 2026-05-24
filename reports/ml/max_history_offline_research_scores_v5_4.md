# Rapport qualite - V5.4 ML offline historique max

## Objectif

V5.4 entraine des baselines ML offline simples sur le dataset historique V5.3 valide.
Ces sorties sont des scores de recherche descriptifs, non actionnables et sans usage de trading.

## Fenetre

- Debut : `2023-03-25`.
- Fin : `2026-05-23`.
- Jours : `1156`.

## Cible et modeles

- Cible : `up_down_flat_h1`.
- Modeles : `majority_class_baseline, random_seeded_baseline, logistic_regression, decision_tree_depth_2`.
- Features : colonnes causales V5.1 autorisees uniquement.
- `walk_forward_group` est conserve pour les metriques descriptives, jamais utilise comme feature.

## Outputs

- `1m` scores : `data/research/v5_4/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/ml-scores.parquet` (6658436 lignes).
  - lignes ML utilisees : `1664609`.
  - train/validation/test : `998754` / `332928` / `332927`.
  - groupes walk-forward : `14`.
- `5m` scores : `data/research/v5_4/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/ml-scores.parquet` (1331588 lignes).
  - lignes ML utilisees : `332897`.
  - train/validation/test : `199726` / `66585` / `66586`.
  - groupes walk-forward : `14`.
- `15m` scores : `data/research/v5_4/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/ml-scores.parquet` (443780 lignes).
  - lignes ML utilisees : `110945`.
  - train/validation/test : `66555` / `22195` / `22195`.
  - groupes walk-forward : `14`.
- `1h` scores : `data/research/v5_4/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/ml-scores.parquet` (110852 lignes).
  - lignes ML utilisees : `27713`.
  - train/validation/test : `16616` / `5548` / `5549`.
  - groupes walk-forward : `14`.

## Sanity checks

- La cible unique est `up_down_flat_h1`.
- Les lignes `warmup_row = true` et `label_valid_h1 = false` sont exclues.
- Les features `future_*`, `label_*`, `direction_*`, `up_down_flat_*`, `split`, `walk_forward_group`, `signal`, `order`, `strategy`, `pnl` et `backtest` sont interdites.
- Les sorties sont nommees `research_*` et ne sont pas des signaux.
- Les metriques sont descriptives : accuracy, balanced accuracy, macro F1, precision/rappel par classe et matrices de confusion.
- Les metriques walk-forward sont descriptives et ne sont pas un backtest.

## Limitations

- V5.4 entraine uniquement des baselines ML offline simples sur le dataset historique V5.3 valide.
- V5.4 produit des metriques descriptives par split et par groupe walk-forward, mais ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Non-usage warnings

- V5.4 ne valide aucune strategie.
- V5.4 ne produit aucun backtest.
- V5.4 ne produit aucun signal de trading.
- V5.4 ne produit aucun ordre.
- V5.4 n'autorise aucun paper live.
- V5.4 n'autorise aucun trading reel.
- Les metriques sont descriptives et non actionnables.
- Les metriques walk-forward ne sont pas un backtest.
