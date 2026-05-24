# Data Card - Galapagos V5.3 Dataset supervise offline historique max

- Dataset name : `max_history_offline_supervised_dataset_v5_3`
- Version : `V5.3`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : `2023-03-25` a `2026-05-23`.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features causales V5.1 OHLCV, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.

## Labels inclus

Labels forward V5.2 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v5_3_preview`.
- Groupes walk-forward descriptifs : trimestre calendaire.

## Known Limitations

- V5.3 assemble uniquement un dataset supervise offline sur la fenetre historique continue validee par V5.0.
- V5.3 prepare des groupes walk-forward descriptifs mais ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V5.3 ne valide aucune strategie.
- V5.3 ne produit aucun modele ML.
- V5.3 ne produit aucun backtest.
- V5.3 ne produit aucun signal de trading.
- V5.3 ne produit aucun ordre.
- V5.3 n'autorise aucun paper live.
- V5.3 n'autorise aucun trading reel.

