# Multi-Day Clean Forward Label Factory V3.1

## Objectif

V3.1 construit uniquement des labels forward multi-day sur BTCUSDT du 2024-01-15 au 2024-01-21, a partir des OHLCV multi-day V2.9 valides.

## Correction V3.1.5

V3.1.5 est une correction smoke-only. V3.1.4 a été refusée en strict uniquement parce que le smoke écrivait ses logs dans le root extrait du ZIP, polluant les validateurs suivants.

V3.1.5 conserve les artefacts fonctionnels V3.1 : mêmes labels, mêmes horizons `[1, 3, 5]`, même threshold `0.0005`, mêmes row counts `10080 / 2016 / 672 / 168`, aucune jointure features + labels et aucun dataset ML.

## Inputs

- Source : OHLCV V2.9 `data/research/v2_9/silver/ohlcv`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `v3_1_20260521T173502Z_0f230165`

## Outputs

- `1m` : `10080` lignes, `data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2024-01-15_2024-01-21/labels.parquet`
- `5m` : `2016` lignes, `data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2024-01-15_2024-01-21/labels.parquet`
- `15m` : `672` lignes, `data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2024-01-15_2024-01-21/labels.parquet`
- `1h` : `168` lignes, `data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2024-01-15_2024-01-21/labels.parquet`

## Horizons et threshold

- Horizons : `[1, 3, 5]`
- Threshold fixe : `0.0005`

## Definition des labels

- `future_close_h` = `close.shift(-h)`.
- `future_simple_return_h` = `future_close_h / close - 1`.
- `future_log_return_h` = `log(future_close_h / close)`.
- `direction_h` vaut `1`, `-1` ou `0` selon le signe du log return.
- `up_down_flat_h` vaut `UP`, `DOWN` ou `FLAT` avec le threshold fixe.

## Colonnes

- `source`
- `venue`
- `market_type`
- `symbol`
- `timeframe`
- `event_ts`
- `close_ts`
- `available_ts`
- `decision_ts`
- `label_available_ts`
- `label_run_id`
- `source_ohlcv_sha256`
- `label_schema_version`
- `future_close_h1`
- `future_log_return_h1`
- `future_simple_return_h1`
- `direction_h1`
- `up_down_flat_h1`
- `label_end_ts_h1`
- `label_valid_h1`
- `future_close_h3`
- `future_log_return_h3`
- `future_simple_return_h3`
- `direction_h3`
- `up_down_flat_h3`
- `label_end_ts_h3`
- `label_valid_h3`
- `future_close_h5`
- `future_log_return_h5`
- `future_simple_return_h5`
- `direction_h5`
- `up_down_flat_h5`
- `label_end_ts_h5`
- `label_valid_h5`
- `label_null_count`
- `label_error_count`
- `tail_row`

## Regles anti-leakage

- Les labels regardent le futur uniquement dans la couche labels separee V3.1.
- Aucune jointure features + labels n'est produite.
- Aucun label n'est ecrit dans `data/research/v3_0/features`.
- `label_available_ts > decision_ts` est verifie pour les lignes avec au moins un horizon valide.
- Les dernieres lignes sans futur suffisant restent marquees invalides par horizon et `tail_row = true`.

## Qualite par timeframe

- `1m` : tail rows `5`, h1 `10079`, h3 `10077`, h5 `10075`, erreurs `0`
- `5m` : tail rows `5`, h1 `2015`, h3 `2013`, h5 `2011`, erreurs `0`
- `15m` : tail rows `5`, h1 `671`, h3 `669`, h5 `667`, erreurs `0`
- `1h` : tail rows `5`, h1 `167`, h3 `165`, h5 `163`, erreurs `0`

## Limitations

- V3.1 produit uniquement des labels forward multi-day separes sur BTCUSDT 2024-01-15 a 2024-01-21 a partir des donnees OHLCV V2.9 validees.
- V3.1 ne produit aucun dataset ML, aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Securite

- V3.1 ne valide aucune stratégie
- V3.1 ne produit aucun dataset ML
- V3.1 ne produit aucun modèle ML
- V3.1 ne produit aucun backtest
- V3.1 ne produit aucun signal de trading
- V3.1 ne produit aucun ordre
- V3.1 n’autorise aucun paper live
- V3.1 n’autorise aucun trading réel

V3.1.5 reste `pending_external_audit`.
