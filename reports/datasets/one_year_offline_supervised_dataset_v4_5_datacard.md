# Data Card - Galapagos V4.5 Dataset supervise offline 1 an

- Dataset name : `one_year_offline_supervised_dataset_v4_5`
- Version : `V4.5`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : 2024-01-01 a 2024-12-31.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features causales V4.3 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.

## Labels inclus

Labels forward V4.4 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v4_5_preview`.

## Known Limitations

- V4.5 assemble uniquement un dataset supervise offline 1 an a partir des features V4.3 et labels V4.4 valides.
- V4.5 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V4.5 ne valide aucune strategie.
- V4.5 ne produit aucun modele ML.
- V4.5 ne produit aucun backtest.
- V4.5 ne produit aucun signal de trading.
- V4.5 ne produit aucun ordre.
- V4.5 n'autorise aucun paper live.
- V4.5 n'autorise aucun trading reel.
