# État du Projet : V3.4.1 validée + candidat V3.5.2

- **Dernière version validée** : V3.4.1.
- **Versions antérieures validées** : V3.3.1, V3.2.1, V3.1.10, V3.0, V2.9.1, V2.8.4, V2.7.2, V2.6.2, V2.5.2, V2.4.8, V2.3.1.
- **Version candidate** : V3.5.2.
- **Statut candidate** : `pending_external_audit`.
- **Direction suivante** : 90-day public market data expansion raw-to-1m validation runtime fix.

## Candidat V3.5.2

- V3.5.2 corrige uniquement le runtime du validateur V3.5.
- V3.5.1 a été refusée en strict parce que `_validate_raw_to_1m` recalculait les dates dans une boucle sur 90 jours et faisait timeout le validateur.
- Le contrôle raw-to-1m reste strict : row count par jour, checksum `raw_file_sha256` par jour et rejet des dates hors fenêtre.
- Les données restent l'expansion publique BTCUSDT sur 90 jours, du 2024-01-01 au 2024-03-30 inclus.
- Outputs OHLCV V3.5 : 1m `129600`, 5m `25920`, 15m `8640`, 1h `2160` lignes.
- V3.5.2 ne produit aucune feature, aucun label, aucun dataset ML et aucun modèle ML.
- V3.5.2 ne produit aucun backtest, aucune stratégie, aucun signal de trading, aucun ordre et aucun trading réel.
- V3.5.2 reste candidate `pending_external_audit`.

## Clause De Sécurité

- Aucun trading réel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune stratégie.
- Aucun signal de trading.
- Aucune feature V3.5.
- Aucun label V3.5.
- Aucun dataset ML V3.5.
- Aucun modèle ML V3.5.
- Aucune API privée.
- Aucune clé API.
- V3.5.2 reste non validée avant audit externe.
