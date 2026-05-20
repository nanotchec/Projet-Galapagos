# Rapport ML offline V2.8

- Correction : `V2.8.2`

## Objectif

V2.8 entraine uniquement des baselines ML offline simples sur le dataset supervise V2.7 valide.
Ces sorties sont des artefacts de recherche descriptifs, non actionnables.

## Target

- Target : `up_down_flat_h1`
- Lignes utilisees : `label_valid_h1 = true` et `warmup_row = false`.

## Features

- `close_lag_1`
- `return_1`
- `log_return_1`
- `return_3`
- `log_return_3`
- `return_5`
- `log_return_5`
- `rolling_vol_5`
- `rolling_vol_15`
- `rolling_vol_30`
- `candle_range`
- `candle_body`
- `upper_wick`
- `lower_wick`
- `close_position_in_range`
- `volume_lag_1`
- `volume_return_1`
- `rolling_volume_mean_5`
- `rolling_volume_mean_15`
- `rolling_volume_zscore_15`
- `sma_5`
- `sma_15`
- `sma_30`
- `close_to_sma_5`
- `close_to_sma_15`
- `close_to_sma_30`
- `hour_utc`
- `day_of_week_utc`
- `is_weekend_utc`
- `feature_null_count`
- `feature_error_count`

## Modeles

- `majority_class_baseline`
- `random_seeded_baseline`
- `logistic_regression`
- `decision_tree_depth_2`

## Qualite

- `1m` : 1409 lignes ML, train=834, validation=288, test=287
- `5m` : 257 lignes ML, train=142, validation=57, test=58
- `15m` : 65 lignes ML, train=27, validation=19, test=19
- `1h` : 0 lignes ML, train=0, validation=0, test=0

## Limitations

- V2.8 entraine uniquement des baselines ML offline simples sur le dataset V2.7 valide.
- V2.8 ne produit aucun backtest, aucune strategie, aucun signal de trading et aucun ordre.

## Securite

- V2.8 ne valide aucune strategie.
- V2.8 ne produit aucun backtest.
- V2.8 ne produit aucun signal de trading.
- V2.8 ne produit aucun ordre.
- V2.8 n'autorise aucun paper live.
- V2.8 n'autorise aucun trading reel.
- Les metriques sont descriptives et non actionnables.
