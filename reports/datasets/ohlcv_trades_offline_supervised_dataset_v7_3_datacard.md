# Data Card - Galapagos V7.3 Dataset supervise offline OHLCV + trades

- Dataset name : `ohlcv_trades_offline_supervised_dataset_v7_3`
- Version : `V7.3`
- Statut : `pending_external_audit`.
- Source : Binance public archive read-only, BTCUSDT spot.
- Periode : `2023-03-25` a `2023-04-23`.
- Timeframes : 1m, 5m, 15m, 1h.

## Features incluses

Features OHLCV + aggTrades V7.2, causales, disponibles a `feature_available_ts` et non posterieures a `decision_ts`.
Les features trades sont des variables de recherche, pas des signaux de trading.

## Labels inclus

Labels forward V5.2 filtres sur la fenetre V7.2, horizons h1, h3 et h5. Les labels sont presents uniquement pour l'analyse offline du dataset.

## Split Policy

- Train : premiers 60 % temporels.
- Validation : 20 % suivants.
- Test : derniers 20 %.
- Aucun shuffle.
- Purge/embargo : `none_v7_3_preview`.
- Groupes walk-forward descriptifs : fenetres de 7 jours.

## Known Limitations

- V7.3 assemble uniquement un dataset supervise offline OHLCV + aggTrades sur une fenetre bornee de 30 jours.
- V7.3 ne produit aucun modele ML, aucun backtest, aucun signal de trading et aucun ordre.

- La fenetre de 30 jours est une preview multi-source, pas une base suffisante pour conclure statistiquement.

## Non-usage Warnings

- V7.3 ne valide aucune strategie.
- V7.3 ne produit aucun modele ML.
- V7.3 ne produit aucun backtest.
- V7.3 ne produit aucun signal de trading.
- V7.3 ne produit aucun ordre.
- V7.3 n'autorise aucun paper live.
- V7.3 n'autorise aucun trading reel.

