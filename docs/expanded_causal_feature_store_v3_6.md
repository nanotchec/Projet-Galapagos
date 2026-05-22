# Expanded Causal Feature Store V3.6

## Objectif

V3.6 construit uniquement un feature store OHLCV causal 90 jours sur BTCUSDT du 2024-01-01 au 2024-03-30, a partir des OHLCV V3.5 valides.

## Inputs

- Source : OHLCV V3.5 `data/research/v3_5/silver/ohlcv`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `v3_6_20260522T093427Z_0d383807`

## Outputs

- `1m` : `129600` lignes, `data/research/v3_6/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-01_2024-03-30/features.parquet`
- `5m` : `25920` lignes, `data/research/v3_6/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-01_2024-03-30/features.parquet`
- `15m` : `8640` lignes, `data/research/v3_6/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-01_2024-03-30/features.parquet`
- `1h` : `2160` lignes, `data/research/v3_6/features/ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-01_2024-03-30/features.parquet`

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

- `1m` : warmup `30`, lignes apres warmup `129570`, erreurs `0`
- `5m` : warmup `30`, lignes apres warmup `25890`, erreurs `0`
- `15m` : warmup `30`, lignes apres warmup `8610`, erreurs `0`
- `1h` : warmup `30`, lignes apres warmup `2130`, erreurs `0`

## Limitations

- V3.6 produit uniquement des features OHLCV causales sur BTCUSDT 2024-01-01 a 2024-03-30 a partir des donnees V3.5 validees.
- V3.6 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

- V3.6 ne valide aucune stratégie
- V3.6 ne produit aucun label
- V3.6 ne produit aucun dataset ML
- V3.6 ne produit aucun modèle ML
- V3.6 ne produit aucun backtest
- V3.6 ne produit aucun signal de trading
- V3.6 ne produit aucun ordre
- V3.6 n’autorise aucun paper live
- V3.6 n’autorise aucun trading réel

V3.6 reste `pending_external_audit`.
