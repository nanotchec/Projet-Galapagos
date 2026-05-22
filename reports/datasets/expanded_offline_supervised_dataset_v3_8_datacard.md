# Data Card - Galapagos V3.8 Dataset supervise offline 90 jours

- Dataset name : `expanded_offline_supervised_dataset_v3_8`
- Version : `V3.8`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : 2024-01-01 a 2024-03-30.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features causales V3.6 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.

## Labels inclus

Labels forward V3.7 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v3_8_preview`.

## Known Limitations

- V3.8 assemble uniquement un dataset supervise offline 90 jours a partir des features V3.6 et labels V3.7 valides.
- V3.8 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V3.8 ne valide aucune strategie.
- V3.8 ne produit aucun modele ML.
- V3.8 ne produit aucun backtest.
- V3.8 ne produit aucun signal de trading.
- V3.8 ne produit aucun ordre.
- V3.8 n'autorise aucun paper live.
- V3.8 n'autorise aucun trading reel.

