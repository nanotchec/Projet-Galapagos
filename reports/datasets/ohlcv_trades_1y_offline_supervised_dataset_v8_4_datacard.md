# Data Card - Galapagos V8.4 Dataset supervise offline OHLCV + trades

- Dataset name : `ohlcv_trades_1y_offline_supervised_dataset_v8_4`
- Version : `V8.4`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : `2023-03-25` a `2024-03-24`.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features OHLCV + aggTrades V8.3, causales, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.
Les features trades sont des variables de recherche, pas des signaux de trading.

## Labels inclus

Labels forward V5.2 filtres sur la fenetre V8.3, horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v8_4_preview`.
- Groupes walk-forward descriptifs : groupes calendaires mensuels de `wf_2023_03_partial` a `wf_2024_03_partial`.

## Known Limitations

- V8.4 assemble uniquement un dataset supervise offline OHLCV + aggTrades sur une fenetre d'environ 1 an.
- V8.4 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

- La fenetre d'environ 1 an permet une analyse plus serieuse que 90 jours, mais ne constitue pas a elle seule une preuve de performance trading.

## Non-usage Warnings

- V8.4 ne valide aucune strategie.
- V8.4 ne produit aucun modele ML.
- V8.4 ne produit aucun backtest.
- V8.4 ne produit aucun signal de trading.
- V8.4 ne produit aucun ordre.
- V8.4 n'autorise aucun paper live.
- V8.4 n'autorise aucun trading reel.
