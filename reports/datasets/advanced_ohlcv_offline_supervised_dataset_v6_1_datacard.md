# Data Card - Galapagos V6.1 Dataset supervise offline advanced OHLCV

- Dataset name : `advanced_ohlcv_offline_supervised_dataset_v6_1`
- Version : `V6.1`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : `2023-03-25` a `2026-05-23`.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Advanced OHLCV features V6.0, causales, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.
La colonne `macd_like_signal` est une feature technique MACD-like, pas un signal de trading.

## Labels inclus

Labels forward V5.2 sur horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v6_1_preview`.
- Groupes walk-forward descriptifs : trimestre calendaire.

## Known Limitations

- V6.1 assemble uniquement un dataset supervise offline a partir des advanced OHLCV features V6.0 et labels V5.2.
- V6.1 prepare des groupes walk-forward descriptifs mais ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

## Non-usage Warnings

- V6.1 ne valide aucune strategie.
- V6.1 ne produit aucun modele ML.
- V6.1 ne produit aucun backtest.
- V6.1 ne produit aucun signal de trading.
- V6.1 ne produit aucun ordre.
- V6.1 n'autorise aucun paper live.
- V6.1 n'autorise aucun trading reel.

