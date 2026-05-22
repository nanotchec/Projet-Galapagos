# Latest Summary

V3.4.1 est la dernière version validée par audit externe.

V3.5 est la candidate courante. Elle étend uniquement les données marché publiques BTCUSDT sur 90 jours, du 2024-01-01 au 2024-03-30 inclus.

Les outputs V3.5 sont écrits sous `data/research/v3_5/silver/ohlcv` avec quatre timeframes : 1m `129600` lignes, 5m `25920` lignes, 15m `8640` lignes et 1h `2160` lignes.

V3.5 vérifie les 90 raw zips publics, les checksums, les timestamps UTC, l'absence de trous et doublons, le schéma `OHLCV_COLUMNS` strict et la cohérence parent-child 1m vers 5m/15m/1h.

V3.5 ne produit aucune feature, aucun label, aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading réel.

V3.5 reste `pending_external_audit`.
