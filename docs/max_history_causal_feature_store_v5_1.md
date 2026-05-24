# Max Historical Causal Feature Store V5.1

## Objectif

V5.1 construit uniquement un feature store OHLCV causal sur la fenetre historique continue validee par V5.0 : `2023-03-25` -> `2026-05-23`, soit `1156` jours.

## Inputs

- Source : OHLCV V5.0 `reports/manifests/max_history_public_market_data_v5_0_manifest.json`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `v5_1_20260524T160246Z_ffdc2c75`

## Outputs

- `1m` : `1664640` lignes, `data/research/v5_1/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/features.parquet`
- `5m` : `332928` lignes, `data/research/v5_1/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/features.parquet`
- `15m` : `110976` lignes, `data/research/v5_1/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/features.parquet`
- `1h` : `27744` lignes, `data/research/v5_1/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/features.parquet`

## Features calculees

- `source`
- `venue`
- `market_type`
- `symbol`
- `timeframe`
- `event_ts`
- `close_ts`
- `available_ts`
- `decision_ts`
- `feature_available_ts`
- `ingested_at_ts`
- `feature_run_id`
- `source_ohlcv_sha256`
- `feature_schema_version`
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
- `warmup_row`
- `feature_null_count`
- `feature_error_count`

## Regles causales

- Les lags et rolling windows utilisent uniquement les observations passees ou courantes.
- Aucun `future_return`, label, target, prediction, signal, order, pnl ou backtest n'est produit.
- `feature_available_ts = available_ts` pour cette preview.
- `decision_ts >= feature_available_ts` est verifie physiquement.

## Warmup

Les 30 premieres lignes de chaque timeframe restent marquees `warmup_row = true` lorsque les lags ou rolling windows critiques ne sont pas encore disponibles. Les NaN de warmup ne sont pas remplis artificiellement.

## Qualite par timeframe

- `1m` : warmup `30`, lignes apres warmup `1664610`, erreurs `0`
- `5m` : warmup `30`, lignes apres warmup `332898`, erreurs `0`
- `15m` : warmup `30`, lignes apres warmup `110946`, erreurs `0`
- `1h` : warmup `30`, lignes apres warmup `27714`, erreurs `0`

## Limitations

- V5.1 produit uniquement des features OHLCV causales sur la fenetre historique continue validee par V5.0.
- V5.1 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

- V5.1 ne valide aucune stratégie
- V5.1 ne produit aucun label
- V5.1 ne produit aucun dataset ML
- V5.1 ne produit aucun modèle ML
- V5.1 ne produit aucun backtest
- V5.1 ne produit aucun signal de trading
- V5.1 ne produit aucun ordre
- V5.1 n’autorise aucun paper live
- V5.1 n’autorise aucun trading réel

V5.1 reste `pending_external_audit`.
