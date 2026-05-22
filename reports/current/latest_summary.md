# Latest Summary

V3.6 est la dernière version validée par audit externe via audit-lite et attestation full locale.

V3.7 est la candidate courante. Elle construit uniquement une label factory forward propre sur la fenêtre BTCUSDT 90 jours, à partir des OHLCV V3.5 validés.

Les inputs restent BTCUSDT spot Binance public archive, fenêtre 2024-01-01 à 2024-03-30 inclus, avec outputs OHLCV V3.5 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160` lignes.

Les outputs V3.7 sont des labels forward séparés dans `data/research/v3_7/labels/forward_returns`, avec row counts 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160`, schéma `LABEL_COLUMNS_V3_7` strict, horizons `[1, 3, 5]` et threshold fixe `0.0005`.

V3.7 ne joint pas features et labels, ne produit aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading réel.

V3.7 reste `pending_external_audit`.
