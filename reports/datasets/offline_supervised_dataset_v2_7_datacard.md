# Data Card - Galapagos V2.7 Offline Supervised Dataset

- Dataset name : `offline_supervised_dataset_v2_7`
- Version : `V2.7`
- Correction candidate : `V2.7.1` runtime validator tests, pending external audit.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : 2024-01-15 uniquement.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features causales V2.5 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.

## Labels inclus

Labels forward V2.6 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.

## Known Limitations

- V2.7 assemble uniquement un dataset supervise offline a partir des features V2.5 et labels V2.6 valides sur BTCUSDT 2024-01-15.
- V2.7 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V2.7 ne valide aucune strategie.
- V2.7 ne produit aucun modele ML.
- V2.7 ne produit aucun backtest.
- V2.7 ne produit aucun signal de trading.
- V2.7 ne produit aucun ordre.
- V2.7 n'autorise aucun paper live.
- V2.7 n'autorise aucun trading reel.
