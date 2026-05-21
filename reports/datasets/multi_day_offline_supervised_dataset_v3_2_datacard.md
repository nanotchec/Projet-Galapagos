# Data Card - Galapagos V3.2 Dataset supervise offline multi-day

- Dataset name : `multi_day_offline_supervised_dataset_v3_2`
- Version : `V3.2`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : 2024-01-15 a 2024-01-21.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features causales V3.0 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.

## Labels inclus

Labels forward V3.1 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v3_2_preview`.

## Known Limitations

- V3.2 assemble uniquement un dataset supervise offline multi-day a partir des features V3.0 et labels V3.1 valides sur BTCUSDT 2024-01-15 a 2024-01-21.
- V3.2 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V3.2 ne valide aucune strategie.
- V3.2 ne produit aucun modele ML.
- V3.2 ne produit aucun backtest.
- V3.2 ne produit aucun signal de trading.
- V3.2 ne produit aucun ordre.
- V3.2 n'autorise aucun paper live.
- V3.2 n'autorise aucun trading reel.
