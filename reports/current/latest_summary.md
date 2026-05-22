# Latest Summary

V3.7 est la dernière version validée par audit externe via audit-lite et attestation full locale.

V3.8 est la candidate courante. Elle assemble uniquement un dataset supervisé offline 90 jours à partir des features causales V3.6 et des labels forward V3.7 validés.

Les inputs restent BTCUSDT spot Binance public archive, fenêtre 2024-01-01 à 2024-03-30 inclus, avec features V3.6 et labels V3.7 strictement séparés.

Les outputs V3.8 sont des datasets et splits séparés dans `data/research/v3_8/datasets/offline_supervised`, avec row counts 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160`, schéma `DATASET_COLUMNS_V3_8` strict et splits temporels train/validation/test sans shuffle.

V3.8 ne produit aucun ML, aucun modèle, aucune prédiction, aucun score ML, aucun backtest, aucune stratégie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading réel.

V3.8 reste `pending_external_audit`.
