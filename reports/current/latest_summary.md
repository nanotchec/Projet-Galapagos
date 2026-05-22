# Latest Summary

V3.5.2 est la dernière version validée par audit externe.

V3.6 est la candidate courante. Elle construit uniquement un feature store OHLCV causal 90 jours à partir des données publiques V3.5.2 validées.

Les inputs restent BTCUSDT spot Binance public archive, fenêtre 2024-01-01 à 2024-03-30 inclus, avec outputs OHLCV V3.5 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160` lignes.

Les outputs V3.6 sont des features OHLCV causales dans `data/research/v3_6/features/ohlcv`, avec row counts 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160`, schéma `FEATURE_COLUMNS_V3_6` strict et warmup de 30 lignes par timeframe.

V3.6 ne produit aucun label, aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading réel.

V3.6 reste `pending_external_audit`.
