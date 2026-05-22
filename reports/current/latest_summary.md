# Latest Summary

V3.4.1 est la dernière version validée par audit externe.

V3.5.2 est la candidate courante. Elle corrige uniquement le runtime du validateur V3.5 en vectorisant le contrôle raw-to-1m.

V3.5.1 a été refusée en strict parce que `_validate_raw_to_1m` recalculait les dates dans une boucle sur 90 jours, ce qui faisait timeout le validateur, les tests validator et le smoke.

Les données restent celles de V3.5 : BTCUSDT spot Binance public archive, fenêtre 2024-01-01 à 2024-03-30 inclus, outputs 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160` lignes.

V3.5.2 ne produit aucune feature, aucun label, aucun dataset ML, aucun modèle ML, aucun backtest, aucune stratégie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading réel.

V3.5.2 reste `pending_external_audit`.
