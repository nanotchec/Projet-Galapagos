# Advanced OHLCV Feature Store V6.0

## Objectif

V6.0 construit uniquement une bibliotheque avancee de features OHLCV causales sur la fenetre historique continue validee par V5.0 : `2023-03-25` -> `2026-05-23`, soit `1156` jours.

Les features avancees sont des variables de recherche. Elles ne sont pas des signaux de trading et ne valident aucune decision operationnelle.

## Inputs

- Source : OHLCV V5.0 `reports/manifests/max_history_public_market_data_v5_0_manifest.json`
- Timeframes : `1m`, `5m`, `15m`, `1h`
- Run : `v6_0_20260524T212547Z_5e1909a5`
- Schema : `V6.0`

## Outputs

- `1m` : `1664640` lignes, `data/research/v6_0/features/advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1m/window=2023-03-25_2026-05-23/features.parquet`
- `5m` : `332928` lignes, `data/research/v6_0/features/advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=5m/window=2023-03-25_2026-05-23/features.parquet`
- `15m` : `110976` lignes, `data/research/v6_0/features/advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=15m/window=2023-03-25_2026-05-23/features.parquet`
- `1h` : `27744` lignes, `data/research/v6_0/features/advanced_ohlcv/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe=1h/window=2023-03-25_2026-05-23/features.parquet`

## Familles de features

- `returns_momentum_multi_horizon` : `18` features
- `volatility_regime` : `17` features
- `trend_moving_averages` : `20` features
- `mean_reversion_zscores` : `10` features
- `breakout_range_donchian` : `21` features
- `bollinger_like` : `10` features
- `candle_anatomy` : `15` features
- `volume_activity` : `16` features
- `taker_buy_imbalance_approx` : `10` features
- `streaks_market_state` : `9` features
- `temporal` : `12` features

## Regles causales

- Tous les calculs utilisent uniquement le passe ou la bougie courante disponible a `decision_ts`.
- Aucun `future_return`, `future_close`, label, target, prediction, order, pnl ou backtest n'est produit.
- La colonne technique `macd_like_signal` est une composante d'indicateur, pas un signal de trading.
- `feature_available_ts = available_ts` pour cette preview.
- `decision_ts >= feature_available_ts` est verifie physiquement.

## Warmup

Les 120 premieres lignes de chaque timeframe restent marquees `warmup_row = true`, car plusieurs indicateurs utilisent des fenetres causales jusqu'a 120 observations. Les NaN de warmup ne sont pas remplis artificiellement.

## Qualite par timeframe

- `1m` : warmup `266`, lignes apres warmup `1664374`, erreurs `0`
- `5m` : warmup `239`, lignes apres warmup `332689`, erreurs `0`
- `15m` : warmup `239`, lignes apres warmup `110737`, erreurs `0`
- `1h` : warmup `239`, lignes apres warmup `27505`, erreurs `0`

## Limitations

- V6.0 produit uniquement des features OHLCV avancees causales sur la fenetre historique continue validee par V5.0.
- V6.0 ne produit aucun label, aucun dataset ML, aucun modele ML, aucun backtest, aucune strategie et aucun ordre.

## Securite

- V6.0 ne valide aucune strategie
- V6.0 ne produit aucun label
- V6.0 ne produit aucun dataset ML
- V6.0 ne produit aucun modele ML
- V6.0 ne produit aucun backtest
- V6.0 ne produit aucun signal de trading
- V6.0 ne produit aucun ordre
- V6.0 n'autorise aucun paper live
- V6.0 n'autorise aucun trading reel
